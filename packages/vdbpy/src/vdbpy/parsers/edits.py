from typing import Any

from vdbpy.types.mappings import edit_event_map
from vdbpy.types.shared import EntryType, UserEdit
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger

logger = get_logger()


def parse_edits_from_archived_versions(
    data: list[dict[Any, Any]], entry_type: EntryType, entry_id: int
) -> list[UserEdit]:
    parsed_edits: list[UserEdit] = []
    version_numbers = [version["version"] for version in data]
    if len(version_numbers) != len(set(version_numbers)):
        logger.warning(
            f"Found duplicate version numbers for {entry_type} entry {entry_id}"
        )
        # https://github.com/VocaDB/vocadb/issues/1990
        return []
    for edit_object in data:
        edit_type = edit_object["reason"]
        debug_line = f"{entry_type} {entry_id} v{edit_object['id']}"
        if edit_type == "Merged":
            logger.debug(f"Merge detected while parsing data for {debug_line}")
            edit_type = "Updated"
        elif edit_type not in edit_event_map:
            logger.debug(f"Unknown edit type '{edit_type}' for {debug_line}")
            edit_type = "Updated"
        else:
            edit_type = edit_event_map[edit_type]
        parsed_edits.append(
            UserEdit(
                user_id=edit_object["author"]["id"],
                edit_date=parse_date(edit_object["created"]),
                entry_type=entry_type,
                entry_id=entry_id,
                version_id=edit_object["id"],
                edit_event=edit_type,
                changed_fields=edit_object["changedFields"],
                update_notes=edit_object["notes"],
            )
        )
    return parsed_edits


def parse_edits(edit_objects: list[dict[Any, Any]]) -> list[UserEdit]:
    logger.debug(f"Got {len(edit_objects)} edits to parse.")
    seen: set[tuple[EntryType, int]] = set()
    parsed_edits: list[UserEdit] = []
    duplicate_count = 0
    skipped_objects: list[Any] = []
    for edit_object in edit_objects:
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
            skipped_objects.append(edit_object)
            continue  # edit object doesn't include archivedVersion

        if "archivedVersion" not in edit_object:
            logger.warning(f"{entry_type}/{entry_id} has no archived version!")
            skipped_objects.append(edit_object)
            continue

        utc_date = edit_object["createDate"]
        version_id = edit_object["archivedVersion"]["id"]

        user_edit = UserEdit(
            user_id=edit_object["archivedVersion"]["author"]["id"],
            edit_date=parse_date(utc_date),
            entry_type=edit_object["entry"]["entryType"],
            entry_id=edit_object["entry"]["id"],
            version_id=version_id,
            edit_event=edit_object["editEvent"],
            changed_fields=edit_object["archivedVersion"]["changedFields"],
            update_notes=edit_object["archivedVersion"]["notes"],
        )

        if (entry_type, version_id) in seen:
            duplicate_count += 1
            continue
        seen.add((entry_type, version_id))
        parsed_edits.append(user_edit)

    logger.debug(f"Found {duplicate_count} duplicates")
    logger.debug(f"Found {len(skipped_objects)} skipped edits:")
    logger.debug(skipped_objects)
    return parsed_edits
