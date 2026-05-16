from pathlib import Path
from classes.io_handler import IOHandler
from functions.file_hashing import group_by_hash
from helpers.console import print_header, print_info, print_success
from models.file_data import FileData


class MediaOrganizerService:
    def __init__(self, *, base_path: str, is_dry_run: bool):
        self.base_path = Path(base_path)
        if not self.base_path.is_dir():
            raise ValueError(f"Invalid directory path: '{base_path}'")
        self.io = IOHandler(base_path=str(base_path), is_dry_run=is_dry_run)
        self.file_data: list[FileData] = []
        self.files: list[Path] = []

    def collect_file_and_hashes(self) -> None:
        self.file_data = self.io.collect_file_data()

    def scan_files(self) -> list[Path]:
        self.files = self.io.scan_files()
        return self.files

    def find_duplicates(self) -> dict[str, list[FileData]]:
        if not self.file_data:
            self.collect_file_and_hashes()

        duplicates = group_by_hash(self.file_data)
        print_success(f"Found {len(duplicates)} groups with duplicates:\n")
        return duplicates

    def move_duplicates(self) -> None:
        duplicates = self.find_duplicates()
        if not duplicates:
            print_info("No duplicates found")
            return
        self.io.move_duplicates(duplicates=duplicates)

    def find_name_conflicts(self) -> dict[str, list[str]]:
        conflicts = self.io.collect_conflicts()
        return conflicts

    def rename_conflicts(self) -> None:
        conflicts = self.find_name_conflicts()
        if not conflicts:
            print_info("No file name conflicts found")
            return
        self.io.rename_conflicts(conflicts=conflicts)

    def sort_files_by_year(self) -> None:
        if not self.files:
            self.scan_files()
        self.io.move_files_to_year(files=self.files)

    def beautify_file_name(self) -> None:
        if not self.files:
            self.scan_files()

        self.io.beautify_file_names(files=self.files)

    def run_all(self) -> None:
        print_header("Starting full operation")
        self.collect_file_and_hashes()
        self.move_duplicates()
        self.rename_conflicts()
        self.sort_files_by_year()
        self.beautify_file_name()
        print_header("All operations completed")
