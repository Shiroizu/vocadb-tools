# ruff: noqa: S101

from typing import get_args

import pytest

from vdbpy.api.search import search_entries
from vdbpy.api.songs import get_song_entries_by_songlist_id
from vdbpy.types.shared import EntryType

KNOWN_PUBLIC_SONGLIST_ID = 16553


@pytest.mark.integration
@pytest.mark.parametrize("entry_type", get_args(EntryType))
def test_search_all_entry_types(entry_type: EntryType) -> None:
    results, total_count = search_entries("Test", entry_type, max_results=1)
    assert len(results) == 1
    assert total_count >= 1


@pytest.mark.integration
def test_get_songlist_songs_by_id() -> None:
    songs = get_song_entries_by_songlist_id(KNOWN_PUBLIC_SONGLIST_ID)
    assert isinstance(songs, list)
    assert len(songs) > 0
    assert "song" in songs[0]
