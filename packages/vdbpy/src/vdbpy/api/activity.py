import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from vdbpy.config import WEBSITE
from vdbpy.types.core import UserEdit
from vdbpy.utils.data import (
    UserEditJSONEncoder,
    get_monthly_count,
    user_edit_from_dict,
)
from vdbpy.utils.date import parse_date
from vdbpy.utils.files import get_text, save_file
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_all_items_between_dates

logger = get_logger()

ACTIVITY_API_URL = f"{WEBSITE}/api/activityEntries"
PARTIAL_SLUG = "-partial"


def get_edits_by_day(year: int, month: int, day: int, save_dir: Path) -> list[UserEdit]:
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
    filename = save_dir / date_str / f"{PARTIAL_SLUG}.json"
    if os.path.isfile(filename):
        logger.debug("Partial save file found.")
        partial_save = True
    else:
        filename = save_dir / f"{date_str}.json"
    if data := get_text(filename):
        logger.debug(f"Loading edits from '{filename}'...")
        previous_edits.extend([user_edit_from_dict(item) for item in json.loads(data)])

        if not partial_save and date.date() < today.date():
            return previous_edits

        if previous_edits:
            date = previous_edits[0].edit_date
            logger.debug(
                f"The most recent saved edit from this date is '{previous_edits[0].edit_date}'"
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
            os.remove(f"{save_dir}/{date_str}{PARTIAL_SLUG}.json")
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

    all_edits = []

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


# --------------------------------------- #


def parse_edits(edit_objects: list[dict]) -> list[UserEdit]:
    logger.debug(f"Got {len(edit_objects)} edits to parse.")
    parsed_edits: list[UserEdit] = []
    for edit_object in edit_objects:
        # logger.debug(f"Parsing edit object {edit_object}")
        entry_type = edit_object["entry"]["entryType"]
        entry_id = edit_object["entry"]["id"]
        if edit_object["editEvent"] == "Deleted":
            # Deletion example: https://vocadb.net/Song/Versions/597650
            if "author" not in edit_object:
                logger.debug(f"Entry {entry_type}/{entry_id} deleted by unknown user")
                continue
            deleter = edit_object["author"]["name"]
            usergroup = edit_object["author"]["groupId"]
            logger.debug(
                f"Entry {entry_type}/{entry_id} deleted by {deleter} ({usergroup})!"
            )
            continue  # edit object doesn't include archivedVersion

        if "archivedVersion" not in edit_object:
            logger.warning(f"{entry_type}/{entry_id} has no archived version!")
            continue

        utc_date = edit_object["createDate"]

        edit_date = parse_date(utc_date)
        version_id = edit_object["archivedVersion"]["id"]
        logger.debug(f"Found edit: {WEBSITE}/{entry_type}/ViewVersion/{version_id}")

        user_edit = UserEdit(
            user_id=edit_object["archivedVersion"]["author"]["id"],
            edit_date=edit_date,
            entry_type=edit_object["entry"]["entryType"],
            entry_id=edit_object["entry"]["id"],
            version_id=version_id,
            edit_event=edit_object["editEvent"],
            changed_fields=edit_object["archivedVersion"]["changedFields"],
            update_notes=edit_object["archivedVersion"]["notes"],
        )
        # logger.debug(f"Edit: {user_edit}")
        parsed_edits.append(user_edit)
    return parsed_edits
