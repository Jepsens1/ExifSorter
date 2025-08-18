import os
import hashlib
from collections import defaultdict
from pathlib import Path
import argparse
import json
import shutil
import piexif
import subprocess


def find_oldest_file(file_group):
    files_with_mtime = []
    for name, path, size in file_group:
        try:
            mtime = os.path.getmtime(path)
            files_with_mtime.append((mtime, path))
        except Exception as e:
            print(f"could not read mtime for {path}: {e}")

    if not files_with_mtime:
        return None
    files_with_mtime.sort()
    return files_with_mtime[0][1]


def move_duplicates(duplicates, base_path):
    dupe_dir = Path(base_path) / "duplicates"
    dupe_dir.mkdir(exist_ok=True)

    for hash_, files in duplicates.items():
        keep_path = find_oldest_file(files)
        print(f"keeping: {keep_path}")

        hash_folder = dupe_dir / hash_
        hash_folder.mkdir(parents=True, exist_ok=True)

        for name, path, size in files:
            if path != keep_path:
                try:
                    target_path = hash_folder / Path(path).name

                    counter = 1
                    while target_path.exists():
                        stem = target_path.stem
                        suffix = target_path.suffix
                        target_path = hash_folder / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(path, target_path)
                    print(f"moved {path} to {target_path}")

                except Exception as e:
                    print(f"could not move file: {path}: {e}")


def hash_file(filepath, chunk_size=8192):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    except Exception as e:
        print(f"could not read file: {filepath} - {e}")
        return None
    return hasher.hexdigest()


def collect_files(base_path):
    file_data = []
    skipped = []
    for filepath in Path(base_path).rglob('*'):
        if filepath.is_file():
            try:
                size = filepath.stat().st_size
                hash_ = hash_file(filepath)
                if hash_:
                    file_data.append((filepath.name, str(filepath), size, hash_))
                else:
                    skipped.append(filepath)
            except Exception as e:
                print(f"failed to collect {filepath}: {e}")
    print(f"total files found: {len(file_data) + len(skipped)}")
    print(f" - files with hash: {len(file_data)}")
    print(f" - files without hash (skipped): {len(skipped)}")
    return file_data


def group_by_hash(file_data):
    hash_groups = defaultdict(list)
    for name, path, size, hash_ in file_data:
        hash_groups[hash_].append((name, path, size))
    # filter so it only keeps groups with duplicates
    return {hash_: files for hash_, files in hash_groups.items() if len(files) > 1}

def print_duplicates(duplicates):
    for hash_, files in duplicates.items():
        print(f"🧬 Hash: {hash_}")
        for name, path, size in files:
            size_mb = size / (1024 * 1024)
            print(f" - {path} ({size_mb:.2f} MB)")
        print("-" * 60)
    print(f"\n🔍 found {len(duplicates)} groups with duplicates:\n")


def print_conflicts(conflicts):
    for name, paths in conflicts.items():
        print(f"{name}")
        for path in paths:
            print(f" - {path}")
        print("-" * 60)
    print(f"found {len(conflicts)} files with same name")


def collect_file_names(base_path):
    name_map = defaultdict(list)

    for filepath in Path(base_path).rglob('*'):
        if filepath.is_file():
            name_map[filepath.name].append(str(filepath))

    conflicts = {name: paths for name, paths in name_map.items() if name != ".DS_Store" and len(paths) > 1}
    return conflicts


def export_duplicates_to_json(duplicates, output_path="duplicates.json"):
    output_data = []
    for hash_, files in duplicates.items():
        entry = {
            "hash": hash_,
            "files": [
                {"name": name, "path": path, "size": size}
                for name, path, size in files
            ]
        }
        output_data.append(entry)

    try:
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"duplicates exported to: {output_path}")
    except Exception as e:
        print(f"failed to write to json: {e}")


def get_exif_datetime(filepath):
    try:
        exif_dict = piexif.load(str(filepath))
        datetime_original = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
        if datetime_original:
            return  datetime_original.decode('utf-8')
    except Exception as e:
        print(f"could not read EXIF for {filepath}: {e}")
    return None


def get_video_creation_date(filepath):
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format_tags=creation_time",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(filepath)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout.strip()
        if output:
            return output.replace('-', '').replace(':','').replace('T', '_')[:15]

        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream_tags=creation_time",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(filepath)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout.strip()
        if output:
            return output.replace('-', '').replace(':', '').replace('T', '_')[:15]
    except Exception as e:
        print(f"metadata fail (video): {filepath.name}: {e}")
    return None


def move_files_to_year(files, base_path):
    counter = 0
    udenexif = Path(base_path) / "withoutexif"
    udenexif.mkdir(exist_ok=True)
    grov_sort = Path(base_path) / "roughly sorted"
    grov_sort.mkdir(exist_ok=True)
    for name, filepath_str, size, hash_ in files:
        filepath = Path(filepath_str)
        if filepath.name == ".DS_Store":
            continue
        datetime_str = get_file_datetime(filepath)
        if not datetime_str:
            new_path = udenexif / name
            if new_path.exists():
                print(f"⚠️ Warning: {new_path.name} already exists in {new_path}")
            else:
                shutil.move(str(filepath), new_path)
                print(f"no exif, move to {new_path}")
                counter += 1
        if datetime_str:
            year = datetime_str[:4]
            year_path = grov_sort / year
            year_path.mkdir(exist_ok=True)
            new_name = f"{datetime_str}_{filepath.stem}{filepath.suffix}"
            new_path = year_path / new_name
            if new_path.exists():
                print(f"⚠️ Warning: {new_path.name} already exists in {year_path}")
            else:
                try:
                   shutil.move(str(filepath), new_path)
                   print(f"{name} has exif with year {year}, moved to {new_path}")
                except Exception as e:
                    print(f"error while moving {e}")
    print(f"files with no exif {counter} out of {len(files)}")


def get_file_datetime(filepath):
    ext = filepath.suffix.lower()
    if ext in ['.jpg', '.jpeg', '.png', '.heic']:
        dt = get_exif_datetime(filepath)
        if dt:
            return dt.replace(':','').replace(' ', '_')
    elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.mod']:
        return get_video_creation_date(filepath)
    return None

def rename_conflicts(conflicts, base_path):
    none_counter = 0
    udenexif = Path(base_path) / "udenexif"
    udenexif.mkdir(exist_ok=True)
    for name, paths in conflicts.items():
        for idx, filepath_str in enumerate(paths, start=1):
            filepath = Path(filepath_str)
            if filepath.name == ".DS_Store":
                continue
            datetime_str = get_file_datetime(filepath)
            if datetime_str:
                new_name = f"{datetime_str}_{filepath.stem}_({idx}){filepath.suffix}"
                new_path = filepath.with_name(new_name)
                counter = 1
                while new_path.exists():
                    new_name = f"{new_path.stem}_({idx})_{counter}{filepath.suffix}"
                    new_path = filepath.with_name(new_name)
                    counter += 1
                print(f"renaming {filepath.name} to {new_path.name}")
                filepath.rename(new_path)
            else:
                none_counter += 1
                new_name = f"ukendt_{filepath.stem}_({idx}){filepath.suffix}"
                new_path = udenexif / new_name
                counter = 1
                while new_path.exists():
                    new_name = f"ukendt_{filepath.stem}_({idx})_{counter}{filepath.suffix}"
                    new_path = udenexif / new_name
                    counter += 1
                print(f"moving {filepath.name} to udenexif as {new_path.name}")
                shutil.move(str(filepath), new_path)
    print(none_counter)


def main():
    parser = argparse.ArgumentParser(prog='image sorter', description='finds duplicates')
    parser.add_argument('folderpath', type=str)
    args = parser.parse_args()


    if not os.path.isdir(args.folderpath):
        print("invalid path")
        return
    print(f'scanning files...can take a while')
    files = collect_files(args.folderpath)



    print("finding duplicates")
    duplicates = group_by_hash(files)

    if duplicates:
        print_duplicates(duplicates)
        move_duplicates(duplicates, args.folderpath)
    else:
        print("no duplicates")

    conflicts = collect_file_names(args.folderpath)
    if conflicts:
        print_conflicts(conflicts)
        rename_conflicts(conflicts, args.folderpath)
    else:
        print(f"no conflicts found")

    move_files_to_year(files, args.folderpath)


if __name__ == "__main__":
    main()