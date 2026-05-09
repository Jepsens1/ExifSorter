from models.file_data import FileData


def print_duplicates(duplicates: dict[str, list[FileData]]):
    for hash_, files in duplicates.items():
        print(f"🧬 Hash: {hash_}")
        for file in files:
            size_mb = file.size / (1024 * 1024)
            print(f" - {file.file_path} ({size_mb:.2f} MB)")
        print("-" * 60)


def print_conflicts(conflicts: dict[str, list[str]]):
    for name, paths in conflicts.items():
        print(f"{name}")
        for path in paths:
            print(f" - {path}")
        print("-" * 60)
