import json
from datetime import UTC, datetime, timedelta

from vdbpy.config import WEBSITE
from vdbpy.types import UserEdit
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


def get_edits_by_day(year: int, month: int, day: int, save_dir="") -> list[UserEdit]:
    date = datetime(year, month, day, tzinfo=UTC)
    date_str = date.strftime("%Y-%m-%d")

    today = datetime.now(tz=UTC)
    if date.date() >= today.date():
        logger.warning(f"Selected date {str(today).split()[0]} is still ongoing or in the future.")
        if save_dir:
            logger.warning(f"Not saving edits to {save_dir} for this day.")
            save_dir = ""
    
    if save_dir:
        filename = f"{save_dir}/{date_str}.json"
        if data := get_text(filename):
            logger.info(f"Loading edits from '{filename}'...")
            return [user_edit_from_dict(item) for item in json.loads(data)]

    params = {"fields": "Entry,ArchivedVersion"}

    day_after = date + timedelta(days=1)

    logger.debug(f"Fetching edits from {date} to {day_after}...")
    edits_by_date = fetch_all_items_between_dates(
        ACTIVITY_API_URL,
        date.strftime("%Y-%m-%d"),
        day_after.strftime("%Y-%m-%d"),
        params=params,
    )
    parsed_edits: list[UserEdit] = parse_edits(edits_by_date)

    logger.debug(f"Found total of {len(edits_by_date)} edits.")

    if save_dir:
        logger.info(f"  Saving edits to '{filename}'...")
        save_file(
            filename,
            json.dumps(
                parsed_edits, cls=UserEditJSONEncoder, indent=4, separators=(",", ":")
            ),
        )

    return parsed_edits


def get_edits_by_month(year=0, month=0, save_dir="") -> list[UserEdit]:
    # Call get_edits_by_day for each day in the month
    if not year or not month:
        today = datetime.now()
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


def get_monthly_top_editors(year: int, month: int, top_n=200) -> list[tuple[int, int]]:
    """Return a sorted list of the top monthly editors: [(user_id, edit_count),..]."""
    edits: list[UserEdit] = get_edits_by_month(year, month)

    edit_counts_by_editor_id: dict[int, int] = {}
    for edit in edits:
        editor_id: int = edit.user_id
        if editor_id in edit_counts_by_editor_id:
            edit_counts_by_editor_id[editor_id] += 1
        else:
            edit_counts_by_editor_id[editor_id] = 1

    return sorted(edit_counts_by_editor_id.items(), key=lambda x: x[1], reverse=True)[
        :top_n
    ]


def get_top_editors_by_field(
    field: str, year: int, month: int, top_n=200
) -> list[tuple[int, int]]:
    """Return a sorted list of the top monthly editors based on an edit field: [(user_id, edit_count),..]."""
    edits: list[UserEdit] = get_edits_by_month(year, month)

    edit_counts_by_editor_id: dict[int, int] = {}
    for edit in edits:
        editor_id: int = edit.user_id
        if field in edit.changed_fields:
            if editor_id in edit_counts_by_editor_id:
                edit_counts_by_editor_id[editor_id] += 1
            else:
                edit_counts_by_editor_id[editor_id] = 1

    return sorted(edit_counts_by_editor_id.items(), key=lambda x: x[1], reverse=True)[
        :top_n
    ]


# --------------------------------------- #


def parse_edits(edit_objects: list[dict]) -> list[UserEdit]:
    logger.debug(f"Got {len(edit_objects)} edits to parse.")
    parsed_edits: list[UserEdit] = []
    for edit_object in edit_objects:
        logger.debug(f"Parsing edit object {edit_object}")
        entry_type = edit_object["entry"]["entryType"]
        entry_id = edit_object["entry"]["id"]
        if edit_object["editEvent"] == "Deleted":
            # Deletion example: https://vocadb.net/Song/Versions/597650
            if "author" not in edit_object:
                logger.debug(
                    f"Entry {entry_type}/{entry_id} deleted by regular user (?)"
                )
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
        local_date = edit_object["archivedVersion"]["created"]
        edit_date = parse_date(utc_date, local_date)
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
        logger.debug(f"Edit: {user_edit}")
        parsed_edits.append(user_edit)
    return parsed_edits
