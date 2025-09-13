from vdbpy.utils.date import get_last_month_strings, month_is_over
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount

logger = get_logger()


def split_list(lst, max_length=50):
    return [lst[i : i + max_length] for i in range(0, len(lst), max_length)]


def truncate_string_with_ellipsis(s, max_length, ending="..."):
    if len(s) > max_length:
        return s[:max_length] + ending

    return s


def add_s(word):
    return word if word.lower().endswith("s") else word + "s"


def get_monthly_count(year: int, month: int, api_url: str, param_name="before") -> int:
    def get_edit_count_before(before_date: str) -> int:
        params = {param_name: before_date}
        return fetch_cached_totalcount(api_url, params=params)

    logger.debug(f"Calculating monthly count for: {year}-{month}")

    a, b = get_last_month_strings(year, month)
    logger.debug(f"Corresponding date strings: {a} - {b}")

    if not month_is_over(year, month):
        raise ValueError(f"Month {month}.{year} is ongoing or in the future!")

    return get_edit_count_before(b) - get_edit_count_before(a)
