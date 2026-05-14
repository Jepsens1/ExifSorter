from pathlib import Path
from classes.io_handler import IOHandler
from functions.file_hashing import group_by_hash
from models.file_data import FileData


class MediaOrganizerService:
    def __init__(self, *, base_path: str):
        self.base_path = Path(base_path)
        if not self.base_path.is_dir():
            raise ValueError(f"Invalid directory path: '{base_path}'")
        self.io = IOHandler(base_path=str(base_path))
        self.file_data: list[FileData] = []
        self.files: list[Path] = []

    def collect_file_and_hashes(self) -> None:
        print("Scanning files and calculating hashes... (this may take a while)")
        self.file_data = self.io.collect_file_data()

    def scan_files(self) -> list[Path]:
        print("Scanning files... (this may take a while)")
        self.files = self.io.scan_files()
        return self.files

    def find_duplicates(self) -> dict[str, list[FileData]]:
        if not self.file_data:
            self.collect_file_and_hashes()

        duplicates = group_by_hash(self.file_data)
        print(f"\n🔍 found {len(duplicates)} groups with duplicates:\n")
        return duplicates

    def move_duplicates(self, *, is_dry_run: bool = False) -> None:
        duplicates = self.find_duplicates()
        if not duplicates:
            print("No duplicates found")
            return
        self.io.move_duplicates(duplicates=duplicates, is_dry_run=is_dry_run)

    def find_name_conflicts(self) -> dict[str, list[str]]:
        conflicts = self.io.collect_conflicts()
        print(f"found {len(conflicts)} files with same name")
        return conflicts

    def rename_conflicts(self, *, is_dry_run: bool = False) -> None:
        conflicts = self.find_name_conflicts()
        if not conflicts:
            print("No file_name conflicts found")
            return
        self.io.rename_conflicts(conflicts=conflicts, is_dry_run=is_dry_run)

    def sort_files_by_year(self, *, is_dry_run: bool = False) -> None:
        if not self.files:
            self.scan_files()
        self.io.move_files_to_year(files=self.files, is_dry_run=is_dry_run)

    def beautify_file_name(self, *, is_dry_run: bool = False) -> None:
        if not self.files:
            self.scan_files()

        self.io.beautify_file_names(files=self.files, is_dry_run=is_dry_run)

    def run_all(self, *, is_dry_run: bool = False) -> None:
        print("=== Starting full operation ===")
        self.collect_file_and_hashes()
        self.move_duplicates(is_dry_run=is_dry_run)
        self.rename_conflicts(is_dry_run=is_dry_run)
        self.sort_files_by_year(is_dry_run=is_dry_run)
        self.beautify_file_name(is_dry_run=is_dry_run)
        print("=== All operations completed ===")
