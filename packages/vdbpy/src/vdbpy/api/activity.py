from vdbpy.config import WEBSITE
from vdbpy.types import UserEdit
from vdbpy.utils.data import get_last_month_strings, get_monthly_count
from vdbpy.utils.date import get_month_strings, parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_all_items_between_dates

logger = get_logger()

ACTIVITY_API_URL = f"{WEBSITE}/api/activityEntries"


# Redundant to cache here as fetch_all_items_between_dates caches already
def get_edits_by_month(year= 0, month = 0) -> list[UserEdit]:
    if not year or not month:
        a, b = get_last_month_strings()
    else:
        a, b = get_month_strings(year, month)
    logger.info(f"Fetching all edits from '{a}' to '{b}'...")
    params = {"fields": "Entry,ArchivedVersion"}
    # Example https://vocadb.net/api/activityEntries?userId=28373&fields=Entry,ArchivedVersion

    all_new_edits = fetch_all_items_between_dates(ACTIVITY_API_URL, a, b, params=params)
    parsed_edits: list[UserEdit] = parse_edits(all_new_edits)

    logger.debug(f"Found total of {len(all_new_edits)} edits.")
    return parsed_edits


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
            edit_object["archivedVersion"]["author"]["id"],
            edit_date,
            edit_object["entry"]["entryType"],
            edit_object["entry"]["id"],
            version_id,
            edit_object["editEvent"],
            edit_object["archivedVersion"]["changedFields"],
        )
        logger.debug(f"Edit: {user_edit}")
        parsed_edits.append(user_edit)
    return parsed_edits
