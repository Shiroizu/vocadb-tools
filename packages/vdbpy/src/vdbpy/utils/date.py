from datetime import UTC, datetime, timedelta

from vdbpy.utils.logger import get_logger

logger = get_logger()


def parse_date(utc_date_str: str, local_date_str: str = "") -> datetime:
    """Convert and parse local date string to utc based on the difference.

    local_date_str has the correct milliseconds as it matches with the version id.

    >>> parse_date("2024-04-06T14:25:28.21Z", "2024-04-06T17:25:28.21")
    datetime.datetime(2024, 4, 6, 14, 25, 28, 210000)
    """
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    short_date_format = "%Y-%m-%d"

    if isinstance(utc_date_str, datetime):
        return utc_date_str  # Sometimes the type checker is confused

    if len(utc_date_str) == 10:
        # 2024-06-01
        return datetime.strptime(utc_date_str, short_date_format)

    utc_date_str = utc_date_str.replace(" ", "T")

    if not utc_date_str.endswith("Z"):
        utc_date_str += "Z"

    if "." not in utc_date_str:
        utc_date_str = utc_date_str.replace("Z", ".0Z")

    if not local_date_str:
        return datetime.strptime(utc_date_str, date_format)

    local_date_str += "Z"

    if "." not in local_date_str:
        local_date_str = local_date_str.replace("Z", ".0Z")

    utc_date = datetime.strptime(utc_date_str, date_format)
    local_date = datetime.strptime(local_date_str, date_format)
    hour_diff = round((utc_date - local_date).total_seconds() / 3600)

    return local_date + timedelta(hours=hour_diff)


def month_is_over(year: int, month: int) -> bool:
    """Verify that the given month is not ongoing or in the future."""
    logger.debug(f"Verifying date {year}-{month}")
    now = datetime.now()
    if year >= now.year and month > now.month:
        logger.warning(f"Current date: {now.month}.{now.year}")
        logger.warning("Selected month is still ongoing or in the future.")
        return False
    return True


def get_month_strings(year: int, month: int) -> tuple[str, str]:
    last_month_string = f"{year}-{str(month).zfill(2)}-01"
    if month == 1:
        month_before_last_month_string = f"{year-1}-12-01"
    else:
        month_before_last_month_string = f"{year}-{str(month-1).zfill(2)}-01"
    return month_before_last_month_string, last_month_string


def get_all_month_strings_since(start_year: int) -> list[tuple[str, str]]:
    """Get list of date string tuples since the start of the input year. Stops before the current month.

    Output: ('2024-01-01', '2024-02-01'), ('2024-02-01', '2024-03-01'), ('2024-03-01', '2024-04-01'), ('2024-04-01', '2024-05-01'), ('2024-05-01', '2024-06-01'), ('2024-06-01', '2024-07-01'), ('2024-07-01', '2024-08-01'), ('2024-08-01', '2024-09-01'), ('2024-09-01', '2024-10-01'), ('2024-10-01', '2024-11-01'), ('2024-11-01', '2024-12-01'), ('2024-12-01', '2025-01-01'), ('2025-01-01', '2025-02-01'), ('2025-02-01', '2025-03-01'), ('2025-03-01', '2025-04-01'), ('2025-04-01', '2025-05-01'), ('2025-05-01', '2025-06-01')]
    """
    now = datetime.now()
    end_month = now.month - 1 if now.month > 1 else 12
    end_year = now.year if now.month > 1 else now.year - 1

    current_month_year = start_year
    current_month = 1
    date_strings = []
    while True:
        if current_month_year >= end_year and current_month >= end_month:
            break

        next_month = current_month + 1 if current_month < 12 else 1
        next_month_year = (
            current_month_year + 1 if current_month == 12 else current_month_year
        )

        a_string = f"{current_month_year}-{str(current_month).zfill(2)}-01"
        b_string = f"{next_month_year}-{str(next_month).zfill(2)}-01"
        date_strings.append((a_string, b_string))

        current_month_year = next_month_year
        current_month = next_month

    return date_strings


def read_timestamp_file(filename: str) -> datetime | None:
    """Read a timestamp from a file, or None if not found."""
    try:
        with open(filename, encoding="utf-8") as file:
            return datetime.fromisoformat(file.read().strip())
    except FileNotFoundError:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(str(datetime.now(UTC)))
        return None
