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

# -------------------- internal -------------------- #


def _load_edits(file: Path) -> list[UserEdit]:
    edits: list[UserEdit] = []
    if Path.is_file(file):
        logger.debug(f"File {file} found.")
        if data := get_text(file):
            edits.extend([user_edit_from_dict(item) for item in json.loads(data)])
        else:
            logger.debug(f"File {file} is empty.")
            logger.debug(f"Removing {file}")
            Path.unlink(file)
    return edits


def _get_edits_with_limit(
    date: datetime, limit: datetime | int | VersionTuple | None = None
) -> tuple[list[UserEdit], bool]:
    def is_correct_version(data: dict[Any, Any]) -> bool:
        entry_type: EntryType = data["entry"]["entryType"]
        version_id: int = (
            data["archivedVersion"]["id"] if "archivedVersion" in data else 0
        )
        assert isinstance(limit, tuple)  # noqa: S101
        return entry_type == limit[0] and version_id == limit[2]

    def is_later_edit(data: dict[Any, Any]) -> bool:
        assert isinstance(limit, datetime)  # noqa: S101
        return parse_date(data["createDate"]) <= limit

    limit_to_use = None
    if isinstance(limit, tuple):
        limit_to_use = is_correct_version

    if isinstance(limit, datetime):
        limit_to_use = is_later_edit

    if isinstance(limit, int):
        limit_to_use = limit

    raw_new_edits, limit_reached = fetch_all_items_between_dates(
        ACTIVITY_API_URL,
        date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        (date + timedelta(days=1)).strftime("%Y-%m-%d"),
        params={"fields": "Entry,ArchivedVersion"},
        limit=limit_to_use,
    )

    return parse_edits(raw_new_edits), limit_reached


def _save_user_edits(filename: Path, edits: list[UserEdit]) -> None:
    save_file(
        filename,
        json.dumps(
            edits,
            cls=UserEditJSONEncoder,
            indent=4,
            separators=(",", ":"),
        ),
    )


def _filter_edits(
    edits: list[UserEdit], limit: datetime | int | VersionTuple
) -> tuple[list[UserEdit], bool]:
    edits_to_return: list[UserEdit] = []
    for edit in edits:
        if isinstance(limit, datetime):
            if edit.edit_date < limit:
                return edits_to_return, True
        elif isinstance(limit, int):
            if len(edits_to_return) == limit:
                return edits_to_return, True
        else:
            entry_type, _, version_id = limit
            if edit.entry_type == entry_type and edit.version_id == version_id:
                return edits_to_return, True
        edits_to_return.append(edit)
    return edits_to_return, False


def _verify_edits(edits: list[UserEdit]) -> None:
    if not edits:
        return
    seen: set[tuple[EntryType, int]] = set()
    prev_edit = None
    for edit in edits:
        edit_key = (edit.entry_type, edit.version_id)
        assert edit_key not in seen, (  # noqa: S101
            f"Duplicate edit {edit_key} found in edits ({len(edits)=}."
        )
        seen.add(edit_key)
        if prev_edit:
            assert edit.edit_date <= prev_edit.edit_date, (edit, prev_edit)  # noqa: S101
            # Matching edit date example:
            # entry_id=851424, version_id=2936993
            # entry_id=851990, version_id=2936994
        prev_edit = edit


def _merge_edit_lists(
    new_edits: list[UserEdit], previous_edits: list[UserEdit]
) -> list[UserEdit]:
    logger.debug(f"Previous edits ({len(previous_edits)}=):")
    if previous_edits:
        logger.debug(
            f"From {previous_edits[0].edit_date} to {previous_edits[-1].edit_date}"
        )
    seen: set[tuple[EntryType, int]] = set()
    duplicate_count = 0
    logger.debug(f"New edits ({len(new_edits)}=):")
    if new_edits:
        logger.debug(f"From {new_edits[0].edit_date} to {new_edits[-1].edit_date}")

    _verify_edits(new_edits)
    _verify_edits(previous_edits)

    combined_edits: list[UserEdit] = []
    for edit_list in (new_edits, previous_edits):
        for edit in edit_list:
            if (edit.entry_type, edit.version_id) in seen:
                duplicate_count += 1
                continue
            seen.add((edit.entry_type, edit.version_id))
            combined_edits.append(edit)

    assert duplicate_count <= 1, duplicate_count  # noqa: S101

    logger.debug(f"Combined edits ({len(combined_edits)}=):")
    if combined_edits:
        logger.debug(
            f"From {combined_edits[0].edit_date} to {combined_edits[-1].edit_date}"
        )
    _verify_edits(combined_edits)
    return combined_edits


def _get_edits_by_current_day(
    date: datetime,
    limit: datetime | int | VersionTuple | None = None,
    partial_filename: Path | None = None,
) -> tuple[list[UserEdit], bool]:
    logger.info(f"Fetching edits until {date} with limit {limit}")

    previous_edits: list[UserEdit] = []
    previous_edits = _load_edits(partial_filename) if partial_filename else []

    since_date = previous_edits[0].edit_date if previous_edits else date
    new_edits, limit_reached = _get_edits_with_limit(since_date, limit)
    logger.debug(f"Found {len(new_edits)} new edits, {limit_reached=}")
    if limit_reached or not previous_edits:
        return new_edits, limit_reached

    combined_edits = _merge_edit_lists(new_edits, previous_edits)

    if partial_filename:
        logger.debug(f"Saving partial edit data to {partial_filename}.")
        _save_user_edits(partial_filename, combined_edits)
    else:
        logger.debug("Not saving partial edit data.")

    if limit is None:
        return combined_edits, False

    return _filter_edits(combined_edits, limit)


def _get_edits_by_past_day(
    date: datetime,
    limit: datetime | int | VersionTuple | None = None,
    filename: Path | None = None,
    partial_filename: Path | None = None,
) -> tuple[list[UserEdit], bool]:
    assert (filename and partial_filename) or (not filename and not partial_filename)  # noqa: S101

    previous_partial_edits = _load_edits(partial_filename) if partial_filename else []
    previous_full_edits = _load_edits(filename) if filename else []

    assert not (previous_partial_edits and previous_full_edits)  # noqa: S101

    edits_to_return: list[UserEdit] = []
    if previous_full_edits:
        edits_to_return = previous_full_edits
    else:
        since_date = (
            previous_partial_edits[0].edit_date if previous_partial_edits else date
        )
        new_edits, limit_reached = _get_edits_with_limit(since_date, limit)
        logger.debug(f"Found {len(new_edits)} new edits, {limit_reached=}")
        if limit_reached:
            return new_edits, limit_reached
        edits_to_return = _merge_edit_lists(new_edits, previous_partial_edits)

    if filename:
        logger.debug(f"Saving edit data to {filename}.")
        _save_user_edits(filename, edits_to_return)
        assert partial_filename  # noqa: S101
        if Path.is_file(partial_filename):
            logger.debug(f"Removing partial edit data {partial_filename}.")
            Path.unlink(partial_filename)
    else:
        logger.debug("Not saving partial edit data.")

    if limit is None:
        return edits_to_return, False

    return _filter_edits(edits_to_return, limit)


# -------------------- public -------------------- #


def get_edits_by_day(
    year: int,
    month: int,
    day: int,
    save_dir: Path | None = None,
    limit: datetime | int | VersionTuple | None = None,
) -> tuple[list[UserEdit], bool]:
    date = datetime(year, month, day, tzinfo=UTC)
    today = datetime.now(tz=UTC)
    if date.date() > today.date():
        logger.debug("Selected date is in the future.")
        return [], True

    date_str = date.strftime("%Y-%m-%d")
    filename = save_dir / f"{date_str}.json" if save_dir else None
    partial_filename = save_dir / f"{date_str}{PARTIAL_SLUG}.json" if save_dir else None

    logger.debug(f"Fetching edits by day {date_str}...")
    logger.debug(f"Limit is {limit}")

    if isinstance(limit, datetime) and limit.date() != date.date():
        logger.info("Ignoring 'limit' date because it is not on this date")
        limit = None

    if date.date() == today.date():
        return _get_edits_by_current_day(date, limit, partial_filename)

    return _get_edits_by_past_day(
        date=date, limit=limit, filename=filename, partial_filename=partial_filename
    )


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
        logger.debug(f"Found {len(current_day_edits)} edits from {date_counter}")
        all_edits.extend(current_day_edits)
        if limit_reached_for_day:
            logger.debug(f"Limit {limit} reached during {date_counter}")
            limit_reached = True
            break
        date_counter -= timedelta(days=1)

    return all_edits, limit_reached


def get_edits_until_day(
    date: datetime, save_dir: Path, limit: datetime | int | VersionTuple | None = None
) -> list[UserEdit]:
    today = datetime.now(tz=UTC)

    logger.debug(f"Today is {today}")
    logger.debug(f"Fetching edits until {date} with limit {limit}")

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
        msg = f"  Found {len(edits_by_day)} edits for {day_to_check_str} (day {day_counter}/{total_days})"
        logger.info(msg)

        all_edits.extend(edits_by_day)
        logger.debug(f"{day_to_check_str} - {limit_reached=}")
        if limit_reached:
            break
        day_to_check -= timedelta(days=1)

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
