# ruff: noqa: S101

from pathlib import Path

import pytest

from vdbpy.api.edits import get_edits_by_entry
from vdbpy.api.entries import (
    get_cached_entry_version,
    get_saved_entry_search,
    read_entries_from_file,
    write_entries_to_file,
)
from vdbpy.api.songs import get_song_by_id
from vdbpy.config import SONG_API_URL
from vdbpy.types.songs import SongVersion


@pytest.mark.integration
def test_matching_entry_and_version() -> None:
    song_id = 1501

    edits = get_edits_by_entry("Song", song_id, include_deleted=True)
    version_data = get_cached_entry_version("Song", edits[0].version_id)
    assert version_data is not None
    assert isinstance(version_data, SongVersion)
    entry_data = get_song_by_id(song_id, fields={"pvs", "artists", "bpm", "lyrics"})
    assert entry_data.length_seconds == version_data.length_seconds
    assert entry_data.original_version_id == version_data.original_version_id
    assert entry_data.publish_date == version_data.publish_date
    assert entry_data.song_type == version_data.song_type
    assert entry_data.pvs != "Unknown"
    assert {pv.pv_id for pv in entry_data.pvs} == {pv.pv_id for pv in version_data.pvs}
    version_artist_ids: set[int] = {a.artist_id for a in version_data.artists}
    assert entry_data.artists != "Unknown"
    entry_artist_ids: set[int] = {
        artist.entry.artist_id
        for artist in entry_data.artists
        if artist.entry != "Custom artist"
    }
    assert version_artist_ids == entry_artist_ids
    assert entry_data.lyrics != "Unknown"
    assert len(entry_data.lyrics) == len(version_data.lyrics)
    assert version_data.max_milli_bpm == entry_data.max_milli_bpm
    assert version_data.min_milli_bpm == entry_data.min_milli_bpm


@pytest.mark.integration
def test_get_saved_entry_search() -> None:
    save_dir = Path("saved_entry_searches")
    save_file = save_dir / "noise_pop_entries.csv"
    noise_pop_tag_id = 7108
    if save_file.is_file():
        save_file.unlink()
    data, counts = get_saved_entry_search(
        save_file,
        SONG_API_URL,
        {"tagId[]": noise_pop_tag_id},
    )
    assert counts == (0, len(data))
    assert len(set(data)) == len(data)
    entries = read_entries_from_file(save_file)
    assert len(entries) == len(data)
    assert len(set(entries)) == len(entries)
    most_5_recent_removed = entries[5:]
    write_entries_to_file(save_file, most_5_recent_removed)
    data2, counts2 = get_saved_entry_search(
        save_file,
        SONG_API_URL,
        {"tagId[]": noise_pop_tag_id, "sort": "AdditionDate"},
    )
    assert len(set(data2)) == len(data2)
    assert counts2 == (len(most_5_recent_removed), 5)
