from datetime import UTC, datetime, timedelta
from pathlib import Path

from vdbpy.utils.logger import get_logger

logger = get_logger()


def parse_date(
    date_to_parse: str,
    date_format: str = "%Y-%m-%dT%H:%M:%S.%fZ",
    short_date_format: str = "%Y-%m-%d",
) -> datetime:
    """Parse various date formats and return datetime with UTC timezone."""
    if len(date_to_parse) == 10:  # noqa: PLR2004
        # 2024-06-02
        return datetime.strptime(date_to_parse, short_date_format).replace(tzinfo=UTC)

    date_to_parse = date_to_parse.strip()
    date_to_parse = date_to_parse.replace(" ", "T")

    offset = None
    offset_sign = 1

    # Handle timezone offset
    if "+" in date_to_parse:
        # Positive offset: 2025-07-21T02:00:00+02:00
        date_to_parse, offset = date_to_parse.split("+")
        offset_sign = 1
    elif date_to_parse.count("-") > 2:  # noqa: PLR2004
        # Negative offset: 2025-07-21T02:00:00-05:00
        parts = date_to_parse.rsplit("-", 1)
        if ":" in parts[1]:
            date_to_parse, offset = parts
            offset_sign = -1

    has_z = date_to_parse.endswith("Z")
    if has_z:
        date_to_parse = date_to_parse[:-1]

    if date_to_parse.count("T") > 1:
        msg = f"Invalid date format: multiple 'T' separators in {date_to_parse}"
        raise ValueError(msg)

    if "." in date_to_parse:
        date_part, microseconds = date_to_parse.rsplit(".", 1)
        microseconds = microseconds.ljust(6, "0")
        date_to_parse = f"{date_part}.{microseconds}"
    else:
        date_to_parse += ".0"

    date_to_parse += "Z"
    parsed = datetime.strptime(date_to_parse, date_format).replace(tzinfo=UTC)

    if offset:
        hours = int(offset.split(":")[0])
        minutes = int(offset.split(":")[1]) if ":" in offset else 0
        offset_delta = timedelta(hours=hours, minutes=minutes)
        parsed -= offset_sign * offset_delta

    return parsed


def month_is_over(year: int, month: int) -> bool:
    """Verify that the given month is not ongoing or in the future."""
    logger.debug(f"Verifying date {year}-{month}")
    now = datetime.now(tz=UTC)
    if year >= now.year and month >= now.month:
        logger.warning(f"Current date: {now.month}.{now.year}")
        logger.warning("Selected month is still ongoing or in the future.")
        return False
    return True


def get_month_strings(year: int, month: int) -> tuple[str, str]:
    """Get datestrings for the current month.

    >>> get_month_strings(2024, 1)
    ('2024-01-01', '2024-02-01')
    >>> get_month_strings(2024, 4)
    ('2024-04-01', '2024-05-01')
    >>> get_month_strings(2024, 12)
    ('2024-12-01', '2025-01-01')
    >>> get_month_strings(3024, 12)
    Traceback (most recent call last):
        ...
    ValueError: Month 12.3024 is ongoing or in the future!
    """
    if not month_is_over(year, month):
        msg = f"Month {month}.{year} is ongoing or in the future!"
        raise ValueError(msg)

    first_day_of_this_month = f"{year}-{str(month).zfill(2)}-01"
    if month == 12:  # noqa: PLR2004
        first_day_of_next_month = f"{year + 1}-01-01"
    else:
        first_day_of_next_month = f"{year}-{str(month + 1).zfill(2)}-01"
    return first_day_of_this_month, first_day_of_next_month


def get_last_month_strings(year: int = 0, month: int = 0) -> tuple[str, str]:
    """Get datestrings for the previous month (current month is still ongoing).

    >>> get_last_month_strings(2024, 1)
    ('2023-12-01', '2024-01-01')
    >>> get_last_month_strings(2024, 5)
    ('2024-04-01', '2024-05-01')
    >>> get_last_month_strings(2024, 12)
    ('2024-11-01', '2024-12-01')
    >>> get_last_month_strings()
    ('2025-08-01', '2025-09-01')
    """
    if not year or not month:
        now = datetime.now(tz=UTC)
        year = now.year
        month = now.month
    first_day_of_this_month = f"{year}-{str(month).zfill(2)}-01"
    if month == 1:
        first_day_of_last_month = f"{year - 1}-12-01"
    else:
        first_day_of_last_month = f"{year}-{str(month - 1).zfill(2)}-01"
    return first_day_of_last_month, first_day_of_this_month


def get_all_month_strings_since(start_year: int) -> list[tuple[str, str]]:
    """Get date strings since the start of the year. Stops before the current month."""
    now = datetime.now(tz=UTC)
    end_month = now.month - 1 if now.month > 1 else 12
    end_year = now.year if now.month > 1 else now.year - 1

    current_month_year = start_year
    current_month = 1
    date_strings: list[tuple[str, str]] = []
    while True:
        if current_month_year >= end_year and current_month >= end_month:
            break

        next_month = current_month + 1 if current_month < 12 else 1  # noqa: PLR2004
        next_month_year = (
            current_month_year + 1 if current_month == 12 else current_month_year  # noqa: PLR2004
        )

        a_string = f"{current_month_year}-{str(current_month).zfill(2)}-01"
        b_string = f"{next_month_year}-{str(next_month).zfill(2)}-01"
        date_strings.append((a_string, b_string))

        current_month_year = next_month_year
        current_month = next_month

    return date_strings


def read_timestamp_file(filename: Path) -> datetime | None:
    """Read a timestamp from a file, or None if not found."""
    try:
        with Path.open(filename, encoding="utf-8") as file:
            return datetime.fromisoformat(file.read().strip())
    except FileNotFoundError:
        with Path.open(filename, "w", encoding="utf-8") as file:
            file.write(str(datetime.now(tz=UTC)))
        return None
