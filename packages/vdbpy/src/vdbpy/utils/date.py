from datetime import datetime, timedelta


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
