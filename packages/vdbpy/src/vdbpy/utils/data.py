from vdbpy.utils.date import get_month_strings, month_is_over
from vdbpy.utils.logger import get_logger

logger = get_logger()


def split_list(lst, max_length=50):
    return [lst[i : i + max_length] for i in range(0, len(lst), max_length)]


def truncate_string_with_ellipsis(s, max_length, ending="..."):
    if len(s) > max_length:
        return s[:max_length] + ending

    return s


def add_s(word):
    return word if word.lower().endswith("s") else word + "s"


def get_monthly_count(year: int, month: int, count_func) -> int:
    logger.debug(f"Calculating monthly count for: {year}-{month}")

    a, b = get_month_strings(year, month)
    logger.debug(f"Corresponding date strings: {a} - {b}")

    month_is_over(year, month)
    return count_func(b) - count_func(a)
