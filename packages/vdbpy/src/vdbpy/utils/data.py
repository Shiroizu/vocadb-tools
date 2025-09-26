import json
from datetime import datetime

from vdbpy.types import UserEdit
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


class UserEditJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for UserEdit objects."""

    def default(self, obj):  # noqa: D102
        if isinstance(obj, UserEdit):
            return {
                "user_id": obj.user_id,
                "edit_date": obj.edit_date.isoformat(),
                "entry_type": obj.entry_type,
                "entry_id": obj.entry_id,
                "version_id": obj.version_id,
                "edit_event": obj.edit_event,
                "changed_fields": obj.changed_fields,
                "update_notes": obj.update_notes,
            }
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def user_edit_from_dict(data: dict) -> UserEdit:
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
