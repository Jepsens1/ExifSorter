import hashlib
from pathlib import Path
from collections import defaultdict
import shutil
from datetime import datetime

from functions.file_metadata import get_file_datetime
from models.file_data import FileData

from helpers.console import (
    print_info,
    print_success,
    print_warning,
    print_error,
    print_dry_run,
    print_header,
)


class IOHandler:
    def __init__(self, *, base_path: str):
        self.base_path: Path = Path(base_path).resolve()
        self.duplicates_dir = self.base_path / "duplicates"
        self.without_exif_dir = self.base_path / "without_exif"
        self.roughly_sorted_dir = self.base_path / "roughly_sorted"

        self.duplicates_dir.mkdir(exist_ok=True)
        self.without_exif_dir.mkdir(exist_ok=True)
        self.roughly_sorted_dir.mkdir(exist_ok=True)

        print_info(f"Initialized IOHandler with base path: {self.base_path}")

    def scan_files(self) -> list[Path]:
        print_header("Scanning files... (this may take a while)")
        return [file for file in self.base_path.rglob("*") if file.is_file()]

    def collect_conflicts(self) -> dict[str, list[str]]:
        names_map: dict[str, list[str]] = defaultdict(list)

        files: list[Path] = self.scan_files()
        print_header("Finding name conflicts")
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

        scanned_files = self.scan_files()
        print_header("Calculating hashes... (this may take a while)")
        for file in scanned_files:
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
                print_error(f"Failed to process {file} - {ex}")
                skipped += 1  # also count as skipped

        total = len(file_data) + skipped
        print_success(f"Summary: Total files: {total}")
        print_info(f" - Files with hash value: {len(file_data)}")
        print_info(f" - Files without hash value (skipped): {skipped}")

        return file_data

    def _find_oldest_file(self, file_group: list[FileData]) -> str:
        files_with_mtime: list[tuple[float, str]] = []
        for file in file_group:
            try:
                mtime = Path(file.file_path).stat().st_mtime
                files_with_mtime.append((mtime, file.file_path))
            except Exception as ex:
                print_error(f"Failed to read mtime for {file.file_path}: {ex}")

        files_with_mtime.sort()
        return files_with_mtime[0][1]

    def move_duplicates(
        self, *, duplicates: dict[str, list[FileData]], is_dry_run: bool
    ) -> None:

        print_header(f"Moving duplicate files to {self.duplicates_dir.name}")
        for hash_value, files in duplicates.items():
            file_to_keep = self._find_oldest_file(files)
            print_info(f"Keeping: {file_to_keep}")

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
                        print_dry_run(f"Would move {file.file_path} to {target_path}")
                    else:
                        shutil.move(file.file_path, target_path)
                        print_success(f"Moved {file.file_path} to {target_path}")

                except Exception as ex:
                    print_error(f"Could not move file: {file.file_path}: {ex}")

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
        print_warning(f"Summary: {none_counter} files without Datetime information")

    def move_files_to_year(self, *, files: list[Path], is_dry_run: bool) -> None:
        no_exif_counter = 0
        for file in files:
            if file.name == ".DS_Store":
                continue
            datetime_str = get_file_datetime(file)
            if datetime_str:
                year = datetime_str[:4]
                year_path = self.roughly_sorted_dir / year
                year_path.mkdir(exist_ok=True)
                new_name = f"{datetime_str}_{file.stem}{file.suffix}"
                new_path = year_path / new_name

                self._save_move(
                    source=file,
                    target=new_path,
                    is_dry_run=is_dry_run,
                    action=f"EXIF -> Year {year}",
                )
            else:
                new_path = self.without_exif_dir / file.name
                no_exif_counter += 1
                self._save_move(
                    source=file,
                    target=new_path,
                    is_dry_run=is_dry_run,
                    action="No EXIF",
                )
        print_warning(
            f"Summary: {no_exif_counter} files moved to: '{self.without_exif_dir.name}'"
        )

    def beautify_file_names(self, *, files: list[Path], is_dry_run: bool) -> None:
        conflict_count = 0
        renamed_count = 0
        for file in files:
            datetime_str = get_file_datetime(file)
            if not datetime_str:
                continue

            try:
                dt = datetime.strptime(datetime_str, "%Y%m%d_%H%M%S")

                format_date = dt.strftime("%d-%m-%Y")
                format_time = dt.strftime("%H-%M-%S")

                parent_folder_name = file.parent.name

                new_name = f"{parent_folder_name}_{format_date}_{format_time}"
                new_path = file.with_name(new_name + file.suffix)

                # Safe guard
                if new_path.exists() and new_path != file:
                    conflict_count += 1
                    counter = 1
                    while new_path.exists():
                        new_path = file.with_name(
                            f"{new_name}_({counter}){file.suffix}"
                        )
                        counter += 1
                    print_warning(
                        f"Conflict detected -> added (_counter) to {file.name}"
                    )
                if is_dry_run:
                    print_dry_run(f"{file.name} -> {new_path.name}")
                else:
                    file.rename(new_path)
                    print_success(f"Beautified: {file.name} → {new_path.name}")

                renamed_count += 1
            except Exception as ex:
                print_error(f"Failed to beautify {file.name}: {ex}")
        print_success(f"Summary: Beautify completed: {renamed_count} files renamed.")
        if conflict_count > 0:
            print_warning(
                f"   → {conflict_count} conflicts resolved with (_1), (_2), etc."
            )

    def _save_move(
        self, *, source: Path, target: Path, is_dry_run: bool, action: str
    ) -> None:
        if target.exists():
            print_warning(f"{target.name} already exists in {target.parent.name}")
            return
        if is_dry_run:
            print_dry_run(f"[{action}]: {source} -> {target}")
        else:
            try:
                shutil.move(str(source), target)
                print_success(f"Moved [{action}]: {source.name} -> {target}")
            except Exception as ex:
                print_error(f"Failed to move {source.name}: {ex}")

    def _hash_file(self, file_path: Path, chunk_size: int = 8192) -> str | None:
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as file:
                while chunk := file.read(chunk_size):
                    hasher.update(chunk)
        except Exception as ex:
            print_error(f"Failed to get hash value for {file_path} - {ex}")
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
            print_dry_run(f"Would rename: {file.name} to {new_path.name}")
        else:
            file.rename(new_path)
            print_success(f"Renamed: {file.name} to {new_path.name}")

    def _move_with_conflict_avoidance(
        self, *, file: Path, target_dir: Path, new_name_base: str, is_dry_run: bool
    ) -> None:

        new_path = target_dir / (new_name_base + file.suffix)
        counter = 1

        while new_path.exists():
            new_path = target_dir / f"{new_name_base}_{counter}{file.suffix}"
            counter += 1
        if is_dry_run:
            print_dry_run(f"Would move: {file.name} to {target_dir} as {new_path.name}")
        else:
            shutil.move(str(file), new_path)
            print_success(f"Moved: {file.name} to {target_dir} as {new_path.name}")
