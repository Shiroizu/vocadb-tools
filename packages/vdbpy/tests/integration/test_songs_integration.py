# ruff: noqa: S101

from datetime import UTC, datetime, timedelta
from typing import get_args

import pytest

from vdbpy.api.songs import (
    SongSearchParams,
    get_song_by_id,
    get_songs,
    get_songs_with_total_count,
)
from vdbpy.types.shared import EntryStatus
from vdbpy.types.songs import Service, SongType

ENTRY_COUNT = 1
QUERY = "kitty"
TAG_IDS = {481, 52}
TAG_NAMES = {"rock", "cat"}
MULTIPLE_SONG_TYPES: set[SongType] = {"Other", "DramaPV"}
CUTOFF = datetime(2025, 1, 1, tzinfo=UTC)
HOURS_MORE_RECENT = 24
ARTIST_IDS = {1, 14}
ARTIST_PARTICIPATION_ID = 20
ORIGINAL_VERSION_ID = 314061
MILLI_BPM_THRESHOLD = 50000
DURATION_THRESHOLD = 300
LANGUAGES = {"fi", "es"}


@pytest.mark.integration
def test_name_query_search() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(query=QUERY, max_results=ENTRY_COUNT),
        fields={"names"},
    )
    for song in songs:
        found = False
        assert song.names != "Unknown"
        for name in song.names.values():
            if QUERY.lower() in name.lower():
                found = True
                break
        assert found, f"S/{song.id} does not contain {QUERY}"


@pytest.mark.integration
@pytest.mark.parametrize("status", get_args(EntryStatus.__value__))
def test_entry_status(status: EntryStatus) -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(status=status, max_results=ENTRY_COUNT),
    )
    for song in songs:
        assert song.status == status


@pytest.mark.integration
@pytest.mark.parametrize("song_type", get_args(SongType.__value__))
def test_song_types(song_type: SongType) -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            song_types={song_type}, max_results=ENTRY_COUNT
        ),
    )
    for song in songs:
        assert song.song_type == song_type


@pytest.mark.integration
def test_multiple_song_types() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            song_types=MULTIPLE_SONG_TYPES, max_results=ENTRY_COUNT
        ),
    )
    for song in songs:
        assert song.song_type in MULTIPLE_SONG_TYPES


@pytest.mark.integration
def test_published_after_date() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            published_after_date=CUTOFF, max_results=ENTRY_COUNT
        ),
    )
    for song in songs:
        assert song.publish_date
        assert song.publish_date > CUTOFF


@pytest.mark.integration
def test_published_before_date() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            published_before_date=CUTOFF, max_results=ENTRY_COUNT
        ),
    )
    for song in songs:
        assert song.publish_date
        assert song.publish_date < CUTOFF


@pytest.mark.integration
def test_addition_dates() -> None:
    today = datetime.now(UTC)
    songs = get_songs(
        song_search_params=SongSearchParams(
            hours_more_recent_than=HOURS_MORE_RECENT,
            max_results=ENTRY_COUNT,
        ),
    )
    cutoff = today - timedelta(days=1)
    for song in songs:
        assert song.create_date > cutoff


@pytest.mark.integration
def test_tag_ids() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(tag_ids=TAG_IDS, max_results=ENTRY_COUNT),
        fields={"tags"},
    )
    for song in songs:
        assert song.tags != "Unknown"
        tag_found = any(tag.tag_id in TAG_IDS for tag in song.tags)
        assert tag_found


@pytest.mark.integration
def test_tag_names() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            tag_names=TAG_NAMES, max_results=ENTRY_COUNT
        ),
        fields={"tags"},
    )
    for song in songs:
        assert song.tags != "Unknown"
        tag_found = any(tag.name in TAG_NAMES for tag in song.tags)
        assert tag_found


@pytest.mark.integration
def test_include_child_tags() -> None:
    parent_tag_id, child_tag_id = 10311, 11310
    songs = get_songs(
        song_search_params=SongSearchParams(
            query="教えてメロディー",
            tag_ids={parent_tag_id},
            max_results=ENTRY_COUNT,
            include_child_tags=True,
        ),
        fields={"tags"},
    )
    for song in songs:
        assert song.tags != "Unknown"
        tag_ids = {tag.tag_id for tag in song.tags}
        assert child_tag_id in tag_ids or parent_tag_id in tag_ids


@pytest.mark.integration
def test_unify_song_types_and_tags() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            query="Three-Eyed Cider",
            song_types={"Cover"},
            tag_ids={2997},
            max_results=ENTRY_COUNT,
            unify_types_and_tags=True,
        ),
        fields={"tags"},
    )
    for song in songs:
        assert song.song_type != "Cover"


@pytest.mark.integration
def test_excluded_tags() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            excluded_tag_ids=TAG_IDS, max_results=ENTRY_COUNT
        ),
        fields={"tags"},
    )
    for song in songs:
        assert song.tags != "Unknown"
        assert not any(tag.tag_id in TAG_IDS for tag in song.tags)


@pytest.mark.integration
def test_artist_ids() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            artist_ids=ARTIST_IDS, max_results=ENTRY_COUNT
        ),
        fields={"artists"},
    )
    for song in songs:
        assert song.artists != "Unknown"
        found_ids = {
            artist.entry.artist_id
            for artist in song.artists
            if artist.entry != "Custom artist"
        }
        assert ARTIST_IDS.issubset(found_ids)


@pytest.mark.integration
def test_artist_participation_status() -> None:
    _, all_count = get_songs_with_total_count(
        song_search_params=SongSearchParams(
            artist_ids={ARTIST_PARTICIPATION_ID},
            max_results=1,
            artist_participation_status="Everything",
        ),
    )
    _, collab_count = get_songs_with_total_count(
        song_search_params=SongSearchParams(
            artist_ids={ARTIST_PARTICIPATION_ID},
            max_results=1,
            artist_participation_status="OnlyCollaborations",
        ),
    )
    assert all_count > collab_count


@pytest.mark.integration
@pytest.mark.slow
def test_include_group_members() -> None:
    group_id = 133928
    _, group_count = get_songs_with_total_count(
        song_search_params=SongSearchParams(artist_ids={group_id}, max_results=1),
    )
    _, member_count = get_songs_with_total_count(
        song_search_params=SongSearchParams(
            artist_ids={group_id}, max_results=1, include_group_members=True
        ),
    )
    assert member_count > group_count


@pytest.mark.integration
def test_only_with_pvs() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            query="Shoveling", only_with_pvs=True, max_results=5
        ),
    )
    assert len(songs) >= 1


@pytest.mark.integration
@pytest.mark.parametrize("service", get_args(Service.__value__))
def test_pv_service(service: Service) -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            pv_service=service, max_results=ENTRY_COUNT
        ),
        fields={"pvs"},
    )
    for song in songs:
        assert song.pvs != "Unknown"
        assert any(pv.pv_service == service for pv in song.pvs)


@pytest.mark.integration
def test_min_score() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(min_score=100, max_results=ENTRY_COUNT),
    )
    for song in songs:
        assert song.rating_score >= 100


@pytest.mark.integration
def test_user_collection_id() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            query="hello world", user_collection_id=329, max_results=5
        ),
    )
    assert len(songs) >= 1


@pytest.mark.integration
def test_release_event_id() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            release_event_id=8281, query="midnight", max_results=5
        ),
    )
    assert len(songs) >= 1


@pytest.mark.integration
def test_original_version_id() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            original_version_id=ORIGINAL_VERSION_ID,
            max_results=ENTRY_COUNT,
        ),
    )
    for song in songs:
        assert song.original_version_id == ORIGINAL_VERSION_ID


@pytest.mark.integration
def test_max_bpm() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            max_milli_bpm=MILLI_BPM_THRESHOLD, max_results=ENTRY_COUNT
        ),
        fields={"bpm"},
    )
    for song in songs:
        assert song.max_milli_bpm != "Unknown"
        assert song.max_milli_bpm is not None
        assert song.max_milli_bpm <= MILLI_BPM_THRESHOLD


@pytest.mark.integration
def test_min_bpm() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            min_milli_bpm=MILLI_BPM_THRESHOLD, max_results=ENTRY_COUNT
        ),
        fields={"bpm"},
    )
    for song in songs:
        assert song.min_milli_bpm != "Unknown"
        assert song.min_milli_bpm is not None
        assert song.min_milli_bpm >= MILLI_BPM_THRESHOLD


@pytest.mark.integration
def test_max_duration() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            max_length=DURATION_THRESHOLD, max_results=ENTRY_COUNT
        ),
    )
    for song in songs:
        assert 0 <= song.length_seconds <= DURATION_THRESHOLD


@pytest.mark.integration
def test_min_duration() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            min_length=DURATION_THRESHOLD, max_results=ENTRY_COUNT
        ),
    )
    for song in songs:
        assert song.length_seconds >= DURATION_THRESHOLD


@pytest.mark.integration
def test_languages() -> None:
    songs = get_songs(
        song_search_params=SongSearchParams(
            languages=LANGUAGES, max_results=ENTRY_COUNT
        ),
        fields={"cultureCodes"},
    )
    for song in songs:
        assert song.languages != "Unknown"
        assert any(lang in LANGUAGES for lang in song.languages)


@pytest.mark.integration
def test_get_song_by_id() -> None:
    song = get_song_by_id(1501, fields={"pvs", "artists", "bpm", "lyrics"})
    assert song.id == 1501
    assert song.default_name
