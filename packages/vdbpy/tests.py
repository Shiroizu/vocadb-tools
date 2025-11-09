# ruff: noqa: S101

import unittest
from datetime import UTC, datetime, timedelta
from typing import get_args

from vdbpy.api.songs import SongSearchParams, get_songs
from vdbpy.types.shared import EntryStatus
from vdbpy.types.songs import SongType
from vdbpy.utils.logger import get_logger

logger = get_logger("test-logger")


class GetSongsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entry_count = 1
        test_tags = {481: "rock", 52: "cat"}
        self.query = "kitty"
        self.cutoff = datetime(2025, 1, 1, tzinfo=UTC)
        self.tag_ids = set(test_tags.keys())
        self.tag_names = set(test_tags.values())

    def test_name_query_search(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                query=self.query, max_results=self.entry_count
            ),
            fields={"names"},
        )
        for song in songs:
            found = False
            assert song.names != "Unknown"
            for name in song.names.values():
                if self.query.lower() in name.lower():
                    found = True
                    break
            assert found, f"S/{song.id} does not contain {self.query}"

    def test_entry_status(self) -> None:
        for status in get_args(EntryStatus):
            songs = get_songs(
                song_search_params=SongSearchParams(
                    status=status, max_results=self.entry_count
                ),
            )
            for song in songs:
                assert song.status == status, (
                    f"S/{song.id} has status {song.status} instead of {status}"
                )

    def test_song_types(self) -> None:
        for song_type in get_args(SongType):
            songs = get_songs(
                song_search_params=SongSearchParams(
                    song_types={song_type}, max_results=self.entry_count
                ),
            )
            for song in songs:
                assert song.song_type == song_type, (
                    f"S/{song.id} has type {song.song_type} instead of {song_type}"
                )

    def test_multiple_song_types(self) -> None:
        song_types: set[SongType] = {"Other", "DramaPV"}
        songs = get_songs(
            song_search_params=SongSearchParams(
                song_types=song_types, max_results=self.entry_count
            ),
        )

        for song in songs:
            assert song.song_type in song_types, (
                f"S/{song.id} has type {song.song_type} instead of {song_types}"
            )

    def test_published_after_date(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                published_after_date=self.cutoff, max_results=self.entry_count
            ),
        )
        for song in songs:
            assert song.publish_date
            assert song.publish_date > self.cutoff, (
                f"S/{song.id}, {song.publish_date} not published after {self.cutoff}"
            )

    def test_published_before_date(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                published_before_date=self.cutoff, max_results=self.entry_count
            ),
        )
        for song in songs:
            assert song.publish_date
            assert song.publish_date < self.cutoff, (
                f"S/{song.id}, {song.publish_date} not published before {self.cutoff}"
            )

    def test_addition_dates(self) -> None:
        today = datetime.now(UTC)
        cutoff = today - timedelta(days=1)
        songs = get_songs(
            song_search_params=SongSearchParams(
                hours_more_recent_than=24, max_results=self.entry_count
            ),
        )
        for song in songs:
            assert song.create_date > cutoff

    def test_tag_ids(self) -> None:
        # multiple tags
        assert len(self.tag_ids) > 1
        songs = get_songs(
            song_search_params=SongSearchParams(
                tag_ids=self.tag_ids, max_results=self.entry_count
            ),
            fields={"tags"},
        )
        for song in songs:
            assert song.tags != "Unknown"
            tag_found = False
            for tag in song.tags:
                if tag.tag_id in self.tag_ids:
                    tag_found = True
                    break
            assert tag_found, f"S/{song.id} does not contain tags {self.tag_ids}"

        # 1 tag
        tag_id = next(iter(self.tag_ids))
        songs = get_songs(
            song_search_params=SongSearchParams(
                tag_ids={tag_id}, max_results=self.entry_count
            ),
            fields={"tags"},
        )
        for song in songs:
            assert song.tags != "Unknown"
            tag_found = False
            for tag in song.tags:
                if tag.tag_id == tag_id:
                    tag_found = True
                    break
            assert tag_found, f"S/{song.id} does not contain tag {tag_id}"

    def test_tag_names(self) -> None:
        # multiple tags
        assert len(self.tag_names) > 1
        songs = get_songs(
            song_search_params=SongSearchParams(
                tag_names=self.tag_names, max_results=self.entry_count
            ),
            fields={"tags"},
        )
        for song in songs:
            assert song.tags != "Unknown"
            tag_found = False
            for tag in song.tags:
                if tag.name in self.tag_names:
                    tag_found = True
                    break
            assert tag_found, f"S/{song.id} does not contain tags {self.tag_names}"

        # 1 tag
        tag_name = next(iter(self.tag_names))
        songs = get_songs(
            song_search_params=SongSearchParams(
                tag_names={tag_name}, max_results=self.entry_count
            ),
            fields={"tags"},
        )
        for song in songs:
            assert song.tags != "Unknown"
            tag_found = False
            for tag in song.tags:
                if tag.name == tag_name:
                    tag_found = True
                    break
            assert tag_found, f"S/{song.id} does not contain tag {tag_name}"

    def test_excluded_tags(self) -> None:
        # multiple tags
        assert len(self.tag_ids) > 1
        songs = get_songs(
            song_search_params=SongSearchParams(
                excluded_tag_ids=self.tag_ids, max_results=self.entry_count
            ),
            fields={"tags"},
        )
        for song in songs:
            assert song.tags != "Unknown"
            tag_found = False
            for tag in song.tags:
                if tag.tag_id in self.tag_ids:
                    tag_found = True
                    break
            assert not tag_found, f"S/{song.id} contains excluded tags {self.tag_ids}"

    def test_include_child_tags(self) -> None:
        # TODO implement
        # for tag_id in self.tag_ids:
        #     child_tags = get_child_tags(tag_id)
        #     assert child_tags
        pass

    """
    11 / 28
    include_child_tags: bool = False  # ! childTags
    unify_types_and_tags: bool = False
    artist_ids: set[int] | None = None  # ! artistId[]
    artist_participation_status: ArtistParticipationStatus | None = None
    include_child_voicebanks: bool = False  # ! childVoicebanks
    include_group_members: bool = False  # ! includeMembers
    only_with_pvs: bool = False
    pv_service: Service | None = None  # ! pvServices
    min_score: int = 0
    user_collection_id: int = 0
    release_event_id: int = 0
    original_version_id: int = 0  # ! parentSongId
    min_bpm: int = 0  # ! minMilliBpm
    max_bpm: int = 0  # ! maxMilliBpm
    min_length: int = 0
    max_length: int = 0
    languages: set[str] | None = None  # ! language --> languages[]
    """


if __name__ == "__main__":
    unittest.main()
