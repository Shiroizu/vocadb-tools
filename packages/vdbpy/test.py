from dataclasses import asdict
from pprint import pprint
from typing import get_args

from vdbpy.api.activity import get_edits_by_day, get_edits_by_entry
from vdbpy.api.entries import get_cached_entry_version, get_entry_link, get_random_entry
from vdbpy.types.core import EntryType
from vdbpy.utils.logger import get_logger

logger = get_logger("test-logger")

# TODO more tests


def test_get_edits_by_day() -> None:
    edit = get_edits_by_day(2025, 10, 15)[0]
    assert edit.version_id == 2883372  # noqa: PLR2004, S101


def test_get_edits_by_entry() -> None:
    edit = get_edits_by_entry("Song", 548301)[0]
    assert edit.version_id == 2883372  # noqa: PLR2004, S101


def test_entry_versions() -> None:
    for entry_type in get_args(EntryType):
        if entry_type == "SongList":
            continue
        if entry_type == "User":
            continue
        logger.info("-" * 39)
        random_entry = get_random_entry(entry_type=entry_type)
        logger.info(get_entry_link(entry_type, random_entry["id"]))
        entry_edits = get_edits_by_entry(entry_type, random_entry["id"])

        most_recent_version = get_cached_entry_version(
            entry_type, entry_edits[0].version_id
        )
        if not most_recent_version:
            logger.info("Most recent version data not availabled.")
            continue

        try:
            pprint(asdict(most_recent_version))  # noqa: T203
        except TypeError:
            logger.info(most_recent_version)


if __name__ == "__main__":
    test_get_edits_by_entry()
