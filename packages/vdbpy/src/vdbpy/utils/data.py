import json
from datetime import datetime
from typing import Any

from vdbpy.types.core import UserEdit
from vdbpy.utils.date import get_last_month_strings, month_is_over
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount

logger = get_logger()


def split_list[T](lst: list[T], max_length: int = 50) -> list[list[T]]:
    return [lst[i : i + max_length] for i in range(0, len(lst), max_length)]


def truncate_string_with_ellipsis(s: str, max_length: int, ending: str = "...") -> str:
    if len(s) > max_length:
        return s[:max_length] + ending

    return s


def add_s(word: str) -> str:
    return word if word.lower().endswith("s") else word + "s"


def get_monthly_count(
    year: int, month: int, api_url: str, param_name: str = "before"
) -> int:
    def get_edit_count_before(before_date: str) -> int:
        params = {param_name: before_date}
        return fetch_cached_totalcount(api_url, params=params)

    logger.debug(f"Calculating monthly count for: {year}-{month}")

    a, b = get_last_month_strings(year, month)
    logger.debug(f"Corresponding date strings: {a} - {b}")

    if not month_is_over(year, month):
        msg = f"Month {month}.{year} is ongoing or in the future!"
        raise ValueError(msg)

    return get_edit_count_before(b) - get_edit_count_before(a)


class UserEditJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for UserEdit objects."""

    def default(self, o: object):  # noqa: ANN201
        if isinstance(o, UserEdit):
            return {
                "user_id": o.user_id,
                "edit_date": o.edit_date.isoformat(),
                "entry_type": o.entry_type,
                "entry_id": o.entry_id,
                "version_id": o.version_id,
                "edit_event": o.edit_event,
                "changed_fields": o.changed_fields,
                "update_notes": o.update_notes,
            }
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def user_edit_from_dict(data: dict[Any, Any]) -> UserEdit:
    return UserEdit(
        user_id=data["user_id"],
        edit_date=datetime.fromisoformat(data["edit_date"]),
        entry_type=data["entry_type"],
        entry_id=data["entry_id"],
        version_id=data["version_id"],
        edit_event=data["edit_event"],
        changed_fields=data["changed_fields"],
        update_notes=data["update_notes"],
    )
