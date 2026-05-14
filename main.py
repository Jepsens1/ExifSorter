import argparse
from classes.media_organizer_service import MediaOrganizerService
from helpers.print_to_console import (
    print_conflicts,
    print_duplicates,
    print_scanned_files,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="image-video-sorter",
        description="Organize images and vidoes, remove duplicates, rename conflicts, sort by year",
    )

    parser.add_argument("dir", type=str, help="Directory to process")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Run all operations")
    group.add_argument("--scan", action="store_true", help="Scan files only")
    group.add_argument("--duplicates", action="store_true", help="Find duplicates")
    group.add_argument("--move-duplicates", action="store_true", help="Move duplicates")
    group.add_argument("--conflicts", action="store_true", help="Find name conflicts")
    group.add_argument(
        "--rename-conflicts", action="store_true", help="Rename conflicts"
    )
    group.add_argument(
        "--sort-year", action="store_true", help="Sort into year folders"
    )
    group.add_argument(
        "--beutify-names",
        action="store_true",
        help="Beutify names into readable file names",
    )

    parser.add_argument("--dry-run", action="store_true", help="Preview only")

    args = parser.parse_args()

    try:
        service = MediaOrganizerService(base_path=args.dir)
    except ValueError as ex:
        print(f"Error: {ex}")
        exit(1)

    if args.all:
        service.run_all(is_dry_run=args.dry_run)
    elif args.scan:
        scanned_files = service.scan_files()
        print_scanned_files(scanned_files)
    elif args.duplicates:
        duplicates = service.find_duplicates()
        print_duplicates(duplicates)
    elif args.move_duplicates:
        service.move_duplicates(is_dry_run=args.dry_run)
    elif args.conflicts:
        conflicts = service.find_name_conflicts()
        print_conflicts(conflicts=conflicts)
    elif args.rename_conflicts:
        service.rename_conflicts(is_dry_run=args.dry_run)
    elif args.sort_year:
        service.sort_files_by_year(is_dry_run=args.dry_run)
    elif args.beutify_names:
        service.beutify_file_name(is_dry_run=args.dry_run)
