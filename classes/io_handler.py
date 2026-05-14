import hashlib
from pathlib import Path
from collections import defaultdict
import shutil

from functions.get_file_datetime import get_file_datetime
from models.file_data import FileData


class IOHandler:
    def __init__(self, *, base_path: str):
        self.base_path = base_path
        self.duplicates_dir = Path(self.base_path) / "duplicates"
        self.duplicates_dir.mkdir(exist_ok=True)
        self.without_exif_dir = Path(self.base_path) / "without_exif"
        self.without_exif_dir.mkdir(exist_ok=True)
        self.roughly_sorted_dir = Path(self.base_path) / "roughly_sorted"
        self.roughly_sorted_dir.mkdir(exist_ok=True)

    def scan_files(self) -> list[Path]:
        return [file for file in Path(self.base_path).rglob("*") if file.is_file()]

    def collect_conflicts(self) -> dict[str, list[str]]:
        names_map: dict[str, list[str]] = defaultdict(list)

        files: list[Path] = self.scan_files()
        for file in files:
            names_map[file.name].append(str(file))

        conflicts = {
            name: paths
            for name, paths in names_map.items()
            if name != ".DS_Store" and len(paths) > 1
        }
        return conflicts

    def collect_file_data(self) -> list[FileData]:
        skipped: int = 0
        file_data: list[FileData] = []

        for file in self.scan_files():
            try:
                size = file.stat().st_size
                hash_value = self._hash_file(file)

                if hash_value:
                    file_data.append(
                        FileData(
                            name=file.name,
                            file_path=str(file),
                            size=size,
                            hash=hash_value,
                        )
                    )
                else:
                    skipped += 1
            except Exception as ex:
                print(f"Failed to process {file} - {ex}")
                skipped += 1  # also count as skipped

        total = len(file_data) + skipped
        print(f"total files found: {total}")
        print(f" - files with hash: {len(file_data)}")
        print(f" - files without hash (skipped): {skipped}")

        return file_data

    def _find_oldest_file(self, file_group: list[FileData]) -> str:
        files_with_mtime: list[tuple[float, str]] = []
        for file in file_group:
            try:
                mtime = Path(file.file_path).stat().st_mtime
                files_with_mtime.append((mtime, file.file_path))
            except Exception as e:
                print(f"could not read mtime for {file.file_path}: {e}")

        files_with_mtime.sort()
        return files_with_mtime[0][1]

    def move_duplicates(
        self, *, duplicates: dict[str, list[FileData]], is_dry_run: bool
    ) -> None:

        for hash_value, files in duplicates.items():
            file_to_keep = self._find_oldest_file(files)
            print(f"keeping: {file_to_keep}")

            hash_folder = self.duplicates_dir / hash_value
            hash_folder.mkdir(parents=True, exist_ok=True)

            for file in files:
                if file.file_path == file_to_keep:
                    continue
                try:
                    target_path = hash_folder / Path(file.file_path).name
                    counter = 1
                    while target_path.exists():
                        stem = target_path.stem
                        suffix = target_path.suffix
                        target_path = hash_folder / f"{stem}_{counter}{suffix}"
                        counter += 1

                    if is_dry_run:
                        print(f"DRY RUN: would move {file.file_path} to {target_path}")
                    else:
                        shutil.move(file.file_path, target_path)
                        print(f"moved {file.file_path} to {target_path}")

                except Exception as e:
                    print(f"could not move file: {file.file_path}: {e}")

    def rename_conflicts(
        self, *, conflicts: dict[str, list[str]], is_dry_run: bool
    ) -> None:
        none_counter = 0
        for name, paths in conflicts.items():
            for idx, path_str in enumerate(paths, start=1):
                file_path = Path(path_str)
                if file_path.name == ".DS_Store":
                    continue
                datetime_str = get_file_datetime(file_path)
                if datetime_str:
                    self._rename_with_conflict_avoidance(
                        file=file_path,
                        new_name_base=f"{datetime_str}_{file_path.stem}_({idx})",
                        is_dry_run=is_dry_run,
                    )
                else:
                    none_counter += 1
                    self._move_with_conflict_avoidance(
                        file=file_path,
                        target_dir=self.without_exif_dir,
                        new_name_base=f"unknown_{file_path.stem}_({idx})",
                        is_dry_run=is_dry_run,
                    )
        print(f"Files without datetime info {none_counter}")

    def move_files_to_year(self, *, files: list[Path], is_dry_run: bool) -> None:
        counter = 0
        for file in files:
            if file.name == ".DS_Store":
                continue
            datetime_str = get_file_datetime(file)
            if not datetime_str:
                new_path = self.without_exif_dir / file.name
                if new_path.exists():
                    print(f"⚠️ Warning: {new_path.name} already exists in {new_path}")
                else:
                    counter += 1
                    if is_dry_run:
                        print(f"DRY RUN: No exif would move to {new_path}")
                    else:
                        shutil.move(str(file), new_path)
                        print(f"no exif, move to {new_path}")
            if datetime_str:
                year = datetime_str[:4]
                year_path = self.roughly_sorted_dir / year
                year_path.mkdir(exist_ok=True)
                new_name = f"{datetime_str}_{file.stem}{file.suffix}"
                new_path = year_path / new_name
                if new_path.exists():
                    print(f"⚠️ Warning: {new_path.name} already exists in {year_path}")
                else:
                    try:
                        if is_dry_run:
                            print(
                                f"DRY RUN: {file.name} has exif with year {year}, moved to {new_path}"
                            )
                        else:
                            shutil.move(str(file), new_path)
                            print(
                                f"{file.name} has exif with year {year}, moved to {new_path}"
                            )
                    except Exception as e:
                        print(f"error while moving {e}")
        print(f"files with no exif {counter} out of {len(files)}")

    def beutify_file_names(self, *, files: list[Path], is_dry_run: bool) -> None:
        print("hello world")

    def _hash_file(self, file_path: Path, chunk_size: int = 8192) -> str | None:
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as file:
                while chunk := file.read(chunk_size):
                    hasher.update(chunk)
        except Exception as ex:
            print(f"Failed to get hash_value for {file_path} - {ex}")
            return None
        return hasher.hexdigest()

    def _rename_with_conflict_avoidance(
        self, *, file: Path, new_name_base: str, is_dry_run: bool
    ) -> None:
        new_path = file.with_name(new_name_base + file.suffix)
        counter = 1
        while new_path.exists():
            new_path = file.with_name(f"{new_name_base}_{counter}{file.suffix}")
            counter += 1
        if is_dry_run:
            print(f"DRY RUN: would rename: {file.name} to {new_path.name}")
        else:
            print(f"Renaming: {file.name} to {new_path.name}")
            file.rename(new_path)

    def _move_with_conflict_avoidance(
        self, *, file: Path, target_dir: Path, new_name_base: str, is_dry_run: bool
    ) -> None:

        new_path = target_dir / (new_name_base + file.suffix)
        counter = 1

        while new_path.exists():
            new_path = target_dir / f"{new_name_base}_{counter}{file.suffix}"
            counter += 1
        if is_dry_run:
            print(
                f"DRY RUN: would move: {file.name} to {target_dir} as {new_path.name}"
            )
        else:
            print(f"Moving: {file.name} to {target_dir} as {new_path.name}")
            shutil.move(str(file), new_path)
