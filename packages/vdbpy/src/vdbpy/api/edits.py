import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from vdbpy.api.entries import get_versions_url, is_entry_deleted
from vdbpy.api.users import find_user_by_username_1d
from vdbpy.config import ACTIVITY_API_URL
from vdbpy.parsers.edits import parse_edits, parse_edits_from_archived_versions
from vdbpy.types.shared import EntryType, UserEdit, VersionTuple
from vdbpy.utils.cache import cache_without_expiration
from vdbpy.utils.data import (
    UserEditJSONEncoder,
    get_monthly_count,
    user_edit_from_dict,
)
from vdbpy.utils.date import parse_date
from vdbpy.utils.files import get_text, save_file
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_all_items_between_dates, fetch_json

logger = get_logger()

PARTIAL_SLUG = "-partial"


def get_edits_by_day(  # noqa: PLR0915
    year: int,
    month: int,
    day: int,
    save_dir: Path | None = None,
    limit: datetime | int | VersionTuple | None = None,
) -> tuple[list[UserEdit], bool]:
    date = datetime(year, month, day, tzinfo=UTC)
    date_str = date.strftime("%Y-%m-%d")

    today = datetime.now(tz=UTC)
    edits_from_today_requested = False

    logger.debug(f"Fetching edits by day {date_str}...")
    logger.debug(f"Limit is {limit}")
    if date.date() > today.date():
        logger.debug("Selected date is in the future.")
        return [], True

    if date.date() == today.date():
        logger.debug("Selected date is today.")
        edits_from_today_requested = True

    if isinstance(limit, datetime) and limit.date() != date.date():
        logger.info("Ignoring 'limit' date because it is not on this date")
        limit = None

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
                if limit is None:
                    return previous_edits, False
                limit_reached = False
                previous_edits_to_return: list[UserEdit] = []
                if isinstance(limit, datetime):
                    for edit in previous_edits:
                        if edit.edit_date < limit:
                            limit_reached = True
                            break
                        previous_edits_to_return.append(edit)
                elif isinstance(limit, int):
                    for edit in previous_edits:
                        if len(previous_edits_to_return) == limit:
                            limit_reached = True
                            break
                        previous_edits_to_return.append(edit)
                elif len(limit) == 3:  # noqa: PLR2004
                    entry_type, _, version_id = limit
                    for edit in previous_edits:
                        if (
                            edit.entry_type == entry_type
                            and edit.version_id == version_id
                        ):
                            break
                        limit_reached = True
                        previous_edits_to_return.append(edit)

                return previous_edits_to_return, limit_reached

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

    def is_correct_version(data: dict[Any, Any]) -> bool:
        assert isinstance(limit, tuple)  # noqa: S101
        entry_type: EntryType = data["entry"]["entryType"]
        version_id: int = (
            data["archivedVersion"]["id"] if "archivedVersion" in data else 0
        )
        return entry_type == limit[0] and version_id == limit[2]

    def is_later_edit(data: dict[Any, Any]) -> bool:
        assert isinstance(limit, datetime)  # noqa: S101
        return parse_date(data["createDate"]) < limit

    limit_to_use = None
    if isinstance(limit, tuple):
        limit_to_use = is_correct_version

    if isinstance(limit, datetime):
        limit_to_use = is_later_edit

    if isinstance(limit, int):
        limit_to_use = limit - len(previous_edits)
        assert limit_to_use > 0  # noqa: S101

    edits_by_date, limit_reached = fetch_all_items_between_dates(
        ACTIVITY_API_URL,
        date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        day_after.strftime("%Y-%m-%d"),
        params=params,
        limit=limit_to_use,
    )

    parsed_edits: list[UserEdit] = parse_edits(edits_by_date)

    prev_length = len(previous_edits)
    if previous_edits:
        for prev_edit in previous_edits:
            if prev_edit not in parsed_edits:
                parsed_edits.append(prev_edit)

    new_edits = len(parsed_edits) - prev_length
    logger.debug(f"Found total of {new_edits} new edits for date {date_str}")

    if limit is not None and limit_reached:
        return parsed_edits, limit_reached

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

    return parsed_edits, limit_reached


def get_edits_by_month(
    year: int,
    month: int,
    save_dir: Path,
    limit: datetime | int | VersionTuple | None = None,
) -> tuple[list[UserEdit], bool]:
    # Call get_edits_by_day for each day in the month
    if not year or not month:
        today = datetime.now(UTC)
        year = today.year
        month = today.month

    all_edits: list[Any] = []

    next_month = month + 1 if month < 12 else 1  # noqa: PLR2004
    next_month_year = year + 1 if next_month == 1 else year

    date_counter = datetime(next_month_year, next_month, 1, tzinfo=UTC)
    date_counter -= timedelta(days=1)

    today = datetime.now(UTC)
    date_counter = min(date_counter, today)

    limit_reached = False
    while True:
        if date_counter.month != month:
            break
        current_day_edits, limit_reached_for_day = get_edits_by_day(
            year, month, date_counter.day, save_dir=save_dir, limit=limit
        )
        all_edits.extend(current_day_edits)
        limit_reached = limit_reached_for_day
        if limit_reached:
            break
        date_counter -= timedelta(days=1)

    return all_edits, limit_reached


def get_edits_until_day(
    date: datetime, save_dir: Path, limit: datetime | int | VersionTuple | None = None
) -> list[UserEdit]:
    today = datetime.now(tz=UTC)
    day_to_check = today
    day_counter = 0

    all_edits: list[UserEdit] = []

    while True:
        day_counter += 1
        if day_to_check < date:
            logger.info(
                f"Edit age thresold {str(date).split()[0]} reached, stopping.\n"
            )
            break
        edits_by_day, limit_reached = get_edits_by_day(
            year=day_to_check.year,
            month=day_to_check.month,
            day=day_to_check.day,
            save_dir=save_dir,
            limit=limit,
        )
        total_days = 1 + (today - date).days
        day_to_check_str = str(day_to_check).split()[0]
        msg = f"  Found {len(edits_by_day)} edits for {day_to_check_str} \
                  (day {day_counter}/{total_days})"
        logger.info(msg)

        all_edits.extend(edits_by_day)
        day_to_check -= timedelta(days=1)
        if limit_reached:
            break

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
        fetch_all_items_between_dates(ACTIVITY_API_URL, params=params, page_size=500)[0]
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
        fetch_all_items_between_dates(ACTIVITY_API_URL, params=params, page_size=500)[0]
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
