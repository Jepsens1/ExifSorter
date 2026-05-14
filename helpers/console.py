from __future__ import annotations


class Colors:
    """ANSI color codes for console output"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"


def print_info(message: str):
    print(f"{Colors.CYAN}{Colors.BOLD}INFO:{Colors.RESET} {message}")


def print_success(message: str):
    print(f"{Colors.GREEN}{Colors.BOLD}SUCCESS:{Colors.RESET} {message}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}{Colors.BOLD}WARNING:{Colors.RESET} {message}")


def print_error(message: str):
    print(f"{Colors.RED}{Colors.BOLD}ERROR:{Colors.RESET} {message}")


def print_dry_run(message: str):
    print(f"{Colors.MAGENTA}{Colors.BOLD}DRY RUN:{Colors.RESET} {message}")


def print_header(message: str):
    print(f"{Colors.BLUE}{Colors.BOLD}=== {message} ==={Colors.RESET}")
