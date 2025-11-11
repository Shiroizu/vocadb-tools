# ruff: noqa: S101, PLR2004

import logging
import unittest
from datetime import UTC, datetime, timedelta
from typing import get_args

from vdbpy.api.edits import get_edits_by_entry
from vdbpy.api.entries import get_cached_entry_version, get_random_entry
from vdbpy.api.songs import SongSearchParams, get_songs, get_songs_with_total_count
from vdbpy.types.shared import EntryStatus, EntryType
from vdbpy.types.songs import Service, SongType
from vdbpy.utils.logger import get_logger

logger = get_logger("test-logger")


class GetSongsTests(unittest.TestCase):
    # TODO rewrite possibly drifting tests

    def setUp(self) -> None:
        logger.info(f"Running test: {self._testMethodName}")
        self.entry_count = 1
        test_tags = {481: "rock", 52: "cat"}
        self.query = "kitty"
        self.multiple_song_types: set[SongType] = {"Other", "DramaPV"}
        self.cutoff = datetime(2025, 1, 1, tzinfo=UTC)
        self.tag_ids = set(test_tags.keys())
        self.tag_names = set(test_tags.values())
        self.hours_more_recent_than = 24
        self.parent_tag_id = 10311
        self.child_tag_id = 11310
        self.artist_ids = {1, 14}
        self.artist_participation_id = 20
        self.parent_vb_id = 1746
        self.child_vb_id = 98816
        self.group_id = 133928
        self.original_version_id = 314061
        self.milli_bpm_thresold = 50000
        self.duration_thresold = 300
        self.languages = {"fi", "es"}

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
        songs = get_songs(
            song_search_params=SongSearchParams(
                song_types=self.multiple_song_types, max_results=self.entry_count
            ),
        )

        for song in songs:
            msg = f"S/{song.id} has type {song.song_type}"
            msg += f" instead of any of {self.multiple_song_types}"
            assert song.song_type in self.multiple_song_types, msg

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
                hours_more_recent_than=self.hours_more_recent_than,
                max_results=self.entry_count,
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
        # can drift in the future
        songs = get_songs(
            song_search_params=SongSearchParams(
                query="教えてメロディー",
                tag_ids={self.parent_tag_id},
                max_results=self.entry_count,
                include_child_tags=True,
            ),
            fields={"tags"},
        )
        for song in songs:
            assert song.tags != "Unknown"
            tag_found = False
            for tag in song.tags:
                if tag.tag_id == self.child_tag_id:
                    tag_found = True
                    break
            assert tag_found, (
                f"S/{song.id} does not contain child tag id {self.child_tag_id}"
            )

    def test_unify_song_types_and_tags(self) -> None:
        # can drift in the future
        songs = get_songs(
            song_search_params=SongSearchParams(
                query="Three-Eyed Cider",
                song_types={"Cover"},
                tag_ids={2997},
                max_results=self.entry_count,
                unify_types_and_tags=True,
            ),
            fields={"tags"},
        )
        for song in songs:
            assert song.song_type != "Cover", (
                f"S/{song.id} has type {song.song_type} instead of something else"
            )

    def test_artist_ids(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                artist_ids=self.artist_ids,
                max_results=self.entry_count,
            ),
            fields={"artists"},
        )
        for song in songs:
            assert song.artists != "Unknown"
            found_artist_ids = {
                artist.entry.artist_id
                for artist in song.artists
                if artist.entry != "Custom artist"
            }
            assert self.artist_ids.issubset(found_artist_ids)

    def test_artist_participation_status(self) -> None:
        # can drift in the future
        _, all_songs_count = get_songs_with_total_count(
            song_search_params=SongSearchParams(
                artist_ids={self.artist_participation_id},
                max_results=1,
                artist_participation_status="Everything",
            ),
        )
        _, collaboration_songs_count = get_songs_with_total_count(
            song_search_params=SongSearchParams(
                artist_ids={self.artist_participation_id},
                max_results=1,
                artist_participation_status="OnlyCollaborations",
            ),
        )
        assert all_songs_count > collaboration_songs_count

    def test_include_child_voicebanks(self) -> None:
        # can drift in the future
        songs = get_songs(
            song_search_params=SongSearchParams(
                query="あなたの墓場に恋をした",
                artist_ids={self.parent_vb_id},
                max_results=1,
                include_child_voicebanks=True,
            ),
            fields={"artists"},
        )
        assert len(songs) == 1
        assert songs[0].artists != "Unknown"
        artist_ids = [
            artist.entry.artist_id
            for artist in songs[0].artists
            if artist.entry != "Custom artist"
        ]
        assert self.child_vb_id in artist_ids

    def test_include_group_members(self) -> None:
        # can drift in the future
        _, group_song_count = get_songs_with_total_count(
            song_search_params=SongSearchParams(
                artist_ids={self.group_id}, max_results=1
            ),
        )
        _, group_member_song_count = get_songs_with_total_count(
            song_search_params=SongSearchParams(
                artist_ids={self.group_id}, max_results=1, include_group_members=True
            ),
        )
        assert group_member_song_count > group_song_count

    def test_only_with_pvs(self) -> None:
        # can drift in the future
        songs = get_songs(
            song_search_params=SongSearchParams(
                query="Shoveling", only_with_pvs=True, max_results=5
            ),
        )
        assert len(songs) == 1

    def test_pv_service(self) -> None:
        for service in get_args(Service):
            songs = get_songs(
                song_search_params=SongSearchParams(
                    pv_service=service, max_results=self.entry_count
                ),
                fields={"pvs"},
            )
            for song in songs:
                service_pv_found = False
                assert song.pvs != "Unknown"
                for pv in song.pvs:
                    if pv.pv_service == service:
                        service_pv_found = True
                assert service_pv_found, f"S/{song.id} does not contain {service}"

    def test_min_score(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                min_score=100, max_results=self.entry_count
            ),
        )
        for song in songs:
            assert song.rating_score >= 100

    def test_user_collection_id(self) -> None:
        # can drift in the future
        songs = get_songs(
            song_search_params=SongSearchParams(
                query="hello world", user_collection_id=329, max_results=5
            ),
        )
        assert len(songs) == 4, "Expected 4 rated songs for user 329 with 'hello world'"

    def test_release_event_id(self) -> None:
        # can drift in the future
        songs = get_songs(
            song_search_params=SongSearchParams(
                release_event_id=8281, query="midnight", max_results=5
            ),
        )
        assert len(songs) == 1, "Expected 1 song for release event 8281 with 'midnight'"

    def test_original_version_id(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                original_version_id=self.original_version_id,
                max_results=self.entry_count,
            ),
        )
        for song in songs:
            assert song.original_version_id == self.original_version_id

    def test_max_bpm(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                max_milli_bpm=self.milli_bpm_thresold, max_results=self.entry_count
            ),
            fields={"bpm"},
        )
        for song in songs:
            assert song.max_milli_bpm != "Unknown"
            assert song.max_milli_bpm
            assert song.max_milli_bpm <= self.milli_bpm_thresold

    def test_min_bpm(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                min_milli_bpm=self.milli_bpm_thresold, max_results=self.entry_count
            ),
            fields={"bpm"},
        )
        for song in songs:
            assert song.min_milli_bpm != "Unknown"
            assert song.min_milli_bpm
            assert song.min_milli_bpm >= self.milli_bpm_thresold

    def test_max_duration(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                max_length=self.duration_thresold, max_results=self.entry_count
            )
        )
        for song in songs:
            assert song.length_seconds >= 0
            assert song.length_seconds <= self.duration_thresold

    def test_min_duration(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                min_length=self.duration_thresold, max_results=self.entry_count
            )
        )
        for song in songs:
            assert song.length_seconds
            assert song.length_seconds >= self.duration_thresold

    def test_languages(self) -> None:
        songs = get_songs(
            song_search_params=SongSearchParams(
                languages=self.languages, max_results=self.entry_count
            ),
            fields={"cultureCodes"},
        )
        for song in songs:
            assert song.languages != "Unknown"
            language_found = False
            for language in song.languages:
                if language in self.languages:
                    language_found = True
                    break
            assert language_found, (
                f"S/{song.id} does not contain languages {self.languages}"
            )


class GetVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        logger.info(f"Running test: {self._testMethodName}")

    def test_entry_versions(self) -> None:
        for entry_type in get_args(EntryType):
            if entry_type in {"SongList", "User"}:
                continue
            entry = get_random_entry(entry_type=entry_type)
            edits = get_edits_by_entry(entry_type, entry["id"], include_deleted=True)
            first_edit = edits[-1]
            assert first_edit.edit_event == "Created"
            assert first_edit.entry_id == entry["id"]
            most_recent_version_id = edits[0].version_id
            most_recent_version_data = get_cached_entry_version(
                entry_type, most_recent_version_id
            )
            assert most_recent_version_data


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)

    unittest.main(failfast=True)
