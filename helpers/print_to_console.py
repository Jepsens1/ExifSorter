from pathlib import Path
from helpers.console import print_info
from models.file_data import FileData


def print_duplicates(duplicates: dict[str, list[FileData]]):
    for hash_, files in duplicates.items():
        print_info(f"Hash: {hash_}")
        for file in files:
            size_mb = file.size / (1024 * 1024)
            print_info(f" - {file.file_path} ({size_mb:.2f} MB)")
        print_info("-" * 60)


def print_conflicts(conflicts: dict[str, list[str]]):
    for name, paths in conflicts.items():
        print_info(f"{name}")
        for path in paths:
            print_info(f" - {path}")
        print_info("-" * 60)


def print_scanned_files(files: list[Path]):
    for file in files:
        size_mb = file.stat().st_size / (1024 * 1024)
        print_info(f"Name: {file.name}   Path: {str(file)}   Size: ({size_mb:.2f} MB)")
