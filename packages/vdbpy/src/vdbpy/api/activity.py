import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from vdbpy.api.entries import get_versions_url, is_entry_deleted
from vdbpy.api.users import find_user_by_username_1d
from vdbpy.config import ACTIVITY_API_URL
from vdbpy.parsers.edits import parse_edits, parse_edits_from_archived_versions
from vdbpy.types.core import EntryType, UserEdit
from vdbpy.utils.cache import cache_without_expiration
from vdbpy.utils.data import (
    UserEditJSONEncoder,
    get_monthly_count,
    user_edit_from_dict,
)
from vdbpy.utils.files import get_text, save_file
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_all_items_between_dates, fetch_json

logger = get_logger()

PARTIAL_SLUG = "-partial"


def get_edits_by_day(
    year: int, month: int, day: int, save_dir: Path | None = None
) -> list[UserEdit]:
    date = datetime(year, month, day, tzinfo=UTC)
    date_str = date.strftime("%Y-%m-%d")

    today = datetime.now(tz=UTC)
    edits_from_today_requested = False

    if date.date() > today.date():
        logger.debug(f"Selected date {date_str} is in the future.")
        return []

    if date.date() == today.date():
        logger.debug(f"Selected date {date_str} is today.")
        edits_from_today_requested = True

    day_after = date + timedelta(days=1)
    partial_save = False
    previous_edits: list[UserEdit] = []
    if save_dir:
        filename = save_dir / date_str / f"{PARTIAL_SLUG}.json"
        if Path.is_file(filename):
            logger.debug("Partial save file found.")
            partial_save = True
        else:
            filename = save_dir / f"{date_str}.json"
        if data := get_text(filename):
            logger.debug(f"Loading edits from '{filename}'...")
            previous_edits.extend(
                [user_edit_from_dict(item) for item in json.loads(data)]
            )

            if not partial_save and date.date() < today.date():
                return previous_edits

            if previous_edits:
                date = previous_edits[0].edit_date
                prev_edit_date = f"{previous_edits[0].edit_date}"
                logger.debug(
                    f"The most recent saved edit from this date is '{prev_edit_date}'"
                )
            else:
                logger.debug("No edits found for this date.")

    params = {"fields": "Entry,ArchivedVersion"}

    logger.info(
        f"Fetching edits from {str(date).split()[0]} to {str(day_after).split()[0]}..."
    )
    edits_by_date = fetch_all_items_between_dates(
        ACTIVITY_API_URL,
        date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        day_after.strftime("%Y-%m-%d"),
        params=params,
    )

    parsed_edits: list[UserEdit] = parse_edits(edits_by_date)

    prev_length = len(previous_edits)
    if previous_edits:
        for prev_edit in previous_edits:
            if prev_edit not in parsed_edits:
                parsed_edits.append(prev_edit)

    new_edits = len(parsed_edits) - prev_length
    logger.debug(f"Found total of {new_edits} new edits for date {date_str}")

    if save_dir:
        if not edits_from_today_requested:
            save_file(
                f"{save_dir}/{date_str}.json",
                json.dumps(
                    parsed_edits,
                    cls=UserEditJSONEncoder,
                    indent=4,
                    separators=(",", ":"),
                ),
            )
            if partial_save:
                Path.unlink(save_dir / "date_str" / PARTIAL_SLUG / ".json")
        else:
            save_file(
                f"{save_dir}/{date_str}{PARTIAL_SLUG}.json",
                json.dumps(
                    parsed_edits,
                    cls=UserEditJSONEncoder,
                    indent=4,
                    separators=(",", ":"),
                ),
            )

    return parsed_edits


def get_edits_by_month(year: int, month: int, save_dir: Path) -> list[UserEdit]:
    # Call get_edits_by_day for each day in the month
    if not year or not month:
        today = datetime.now(UTC)
        year = today.year
        month = today.month

    all_edits: list[Any] = []

    date_counter = datetime(year, month, 1, tzinfo=UTC)
    while True:
        if date_counter.month != month:
            break
        current_day_edits = get_edits_by_day(year, month, date_counter.day, save_dir)
        all_edits.extend(current_day_edits)
        date_counter += timedelta(days=1)

    return all_edits


def get_monthly_edit_count(year: int, month: int) -> int:
    return get_monthly_count(year, month, ACTIVITY_API_URL)


def get_created_entries_by_username(username: str) -> list[UserEdit]:
    # Also includes deleted entries
    username, user_id = find_user_by_username_1d(username)
    params = {
        "userId": user_id,
        "fields": "Entry,ArchivedVersion",
        "editEvent": "Created",
    }

    logger.debug(f"Fetching created entries by user '{username}' ({user_id})")
    return parse_edits(
        fetch_all_items_between_dates(ACTIVITY_API_URL, params=params, page_size=500)
    )


def get_edits_by_username(username: str) -> list[UserEdit]:
    # Also includes deleted entries
    username, user_id = find_user_by_username_1d(username)
    params = {
        "userId": user_id,
        "fields": "Entry,ArchivedVersion",
    }

    logger.debug(f"Fetching edits by user '{username}' ({user_id})")
    return parse_edits(
        fetch_all_items_between_dates(ACTIVITY_API_URL, params=params, page_size=500)
    )


def get_most_recent_edit_by_user_id(user_id: int) -> UserEdit:
    params = {"userId": user_id, "fields": "Entry,ArchivedVersion", "maxResults": 1}

    logger.debug(f"Fetching most recent edit by user id '{user_id}'")
    return parse_edits(fetch_json(ACTIVITY_API_URL, params=params)["items"])[0]


def get_edits_by_entry(
    entry_type: EntryType, entry_id: int, include_deleted: bool = False
) -> list[UserEdit]:
    data = fetch_json(get_versions_url(entry_type, entry_id))
    if not include_deleted:
        if entry_type in ["Album", "Tag", "ReleaseEvent", "ReleaseEventSeries"]:
            if is_entry_deleted(entry_type, entry_id):
                logger.debug(f"{entry_type} {entry_id} has been deleted.")
                return []

        elif "deleted" in data["entry"] and data["entry"]["deleted"]:
            logger.debug(f"{entry_type} {entry_id} has been deleted.")
            return []

    return parse_edits_from_archived_versions(
        data["archivedVersions"], entry_type, entry_id
    )


@cache_without_expiration()
def get_cached_edits_by_entry_before_version_id(
    entry_type: EntryType, entry_id: int, version_id: int, include_deleted: bool = False
) -> list[UserEdit]:
    edits = get_edits_by_entry(entry_type, entry_id, include_deleted)
    return [edit for edit in edits if edit.version_id <= version_id]
