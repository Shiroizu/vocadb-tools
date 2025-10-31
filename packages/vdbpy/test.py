import datetime
from dataclasses import asdict
from pprint import pprint
from typing import get_args

from vdbpy.api.activity import get_edits_by_day, get_edits_by_entry
from vdbpy.api.entries import get_cached_entry_version, get_entry_link, get_random_entry
from vdbpy.types.core import EntryType, UserEdit


def test_get_edits_by_day() -> None:
    assert get_edits_by_day(2025, 10, 15)[0] == UserEdit(  # noqa: S101
        user_id=30280,
        edit_date=datetime.datetime(
            2025, 10, 15, 23, 56, 9, 443000, tzinfo=datetime.timezone.utc
        ),
        entry_type="Song",
        entry_id=548301,
        version_id=2883372,
        edit_event="Updated",
        changed_fields=["PVs"],
        update_notes="",
    )


def test_get_edits_by_entry() -> None:
    assert get_edits_by_entry("Song", 548301)[0] == UserEdit(  # noqa: S101
        user_id=30280,
        edit_date=datetime.datetime(
            2025, 10, 16, 1, 56, 9, 443000, tzinfo=datetime.timezone.utc
        ),
        entry_type="Song",
        entry_id=548301,
        version_id=2883372,
        edit_event="Updated",
        changed_fields=["PVs"],
        update_notes="",
    )


def test_entry_versions() -> None:
    for entry_type in get_args(EntryType):
        if entry_type == "SongList":
            continue
        if entry_type == "User":
            continue
        print("-" * 39)
        random_entry = get_random_entry(entry_type=entry_type)
        print(get_entry_link(entry_type, random_entry["id"]))
        entry_edits = get_edits_by_entry(entry_type, random_entry["id"])

        most_recent_version = get_cached_entry_version(
            entry_type, entry_edits[0].version_id
        )
        if not most_recent_version:
            print("Most recent version data not availabled.")
            continue

        try:
            pprint(asdict(most_recent_version))  # noqa: T203
        except TypeError:
            print(most_recent_version)


if __name__ == "__main__":
    test_get_edits_by_entry()
