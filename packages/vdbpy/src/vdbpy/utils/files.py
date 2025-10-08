import os
import sys
from pathlib import Path

from vdbpy.utils.console import get_credentials_from_console, prompt_choice
from vdbpy.utils.logger import get_logger

logger = get_logger()


def verify_file(filename: str) -> None:
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not os.path.isfile(filename):
        logger.debug(f"File '{filename}' not found. Creating an empty file.")
        with open(filename, "w") as f:
            f.write("")


def get_text(filename: str) -> str:
    """Safely read lines from a file. Create file and return an empty list if necessary."""
    verify_file(filename)

    logger.debug(f"Fetching lines from file '{filename}'")
    with open(filename, encoding="utf8") as f:
        return f.read()


def get_lines(filename: str) -> list[str]:
    """Safely read lines from a file. Create file and return an empty list if necessary."""
    verify_file(filename)

    logger.debug(f"Fetching lines from file '{filename}'")
    with open(filename, encoding="utf8") as f:
        return f.read().splitlines()


def get_credentials(
    credentials_path: str, account_name: str = "", get_all=False
) -> dict | tuple[str, str]:
    """Load credentials from the credentials file.

    -------- file start
    username
    password

    username2
    password2
    -------- file end

    Multiple credentials are separated by an empty line.
    """
    credentials = {}

    lines = get_lines(credentials_path)
    lines = [line.strip() for line in lines if line.strip()]

    if len(lines) % 2 != 0:
        logger.warning("Credentials file has an odd number of non-empty lines!")
        sys.exit()

    for i in range(0, len(lines), 2):
        account = lines[i]
        password = lines[i + 1]
        credentials[account] = password

    if get_all:
        return credentials

    if not credentials:
        logger.warning("Credentials not found")
        logger.warning(
            "Create a 'credentials.env' to skip this step, with the following format:"
        )
        logger.warning("------------------------------")
        logger.warning("account_name")
        logger.warning("password")
        logger.warning("------------------------------\n")

        # get from console:
        return get_credentials_from_console()

    if account_name:
        if account_name in credentials:
            return (account_name, credentials[account_name])

        logger.warning(f"Credentials for '{account_name}' not found")
        sys.exit(0)

    if len(credentials) == 1:
        acc, pw = next(iter(credentials.items()))
        return (str(acc), str(pw))

    selected_account = prompt_choice(list(credentials.keys()))
    return (selected_account, credentials[selected_account])


def sanitize_filename(filename: str) -> str:
    chars_to_replace = '\\/:*?<>|"'
    translation_table = str.maketrans({ch: "_" for ch in chars_to_replace})
    sanitized = filename.translate(translation_table)
    if filename != sanitized:
        logger.info("Sanitized filename:")
        logger.info(f"Before: '{filename}'")
        logger.info(f"After: '{sanitized}'")
    return sanitized


def save_file(filepath: str, content: str | list, append=False) -> None:
    """Safely writes content to a file, creating necessary directories."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"

    if isinstance(content, list):
        content_to_write = "\n".join(list(map(str, content)))
    else:
        content_to_write = str(content)

    with path.open(mode, encoding="utf-8") as f:
        if append:
            f.write("\n")
        f.write(content_to_write)

    logger.debug(f"File saved: '{filepath}'")


def clear_file(filepath: str):
    """Clear file if it exists."""
    save_file(filepath, "", append=False)


def write_dict(filename: str, data: dict, separator=":"):
    """Write dict keys and values to a file."""
    lines = [f"{key}{separator}{value}" for key, value in data.items()]
    save_file(filename, lines)


def replace_line_in_file(
    filename: str, old_line: str, new_line: str, count=1, startswith=False
):
    logger.debug(f"Replacing line on file '{filename}'")
    logger.debug(f"Old line: {old_line}")
    logger.debug(f"New line: {new_line}")
    lines = get_lines(filename)
    counter = count
    new_lines = []
    for line in lines:
        condition = line.startswith(old_line) if startswith else (line == old_line)
        if condition and counter > 0:
            if new_line:
                new_lines.append(new_line)
            counter -= 1
        else:
            new_lines.append(line)

    save_file(filename, new_lines)


def remove_line_from_file(filename: str, line_to_remove: str, count=1, starswith=False):
    replace_line_in_file(filename, line_to_remove, "", count, starswith)
