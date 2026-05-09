from collections import defaultdict

from models.file_data import FileData


def group_by_hash(file_data: list[FileData]) -> dict[str, list[FileData]]:
    hash_groups: dict[str, list[FileData]] = defaultdict(list)

    for file in file_data:
        hash_groups[file.hash].append(file)
    # filter so it only keeps groups with duplicates
    return {h: files for h, files in hash_groups.items() if len(files) > 1}
