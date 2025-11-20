# ruff: noqa: S101, PLR2004

import logging
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import get_args

from vdbpy.api.edits import (
    get_edits_by_day,
    get_edits_by_entry,
    get_edits_by_month,
    get_edits_until_day,
)
from vdbpy.api.entries import (
    get_cached_entry_version,
    get_random_entry,
    get_saved_entry_search,
    read_entries_from_file,
    write_entries_to_file,
)
from vdbpy.api.songs import (
    SongSearchParams,
    get_song_by_id,
    get_songs,
    get_songs_with_total_count,
)
from vdbpy.config import SONG_API_URL
from vdbpy.types.shared import EntryStatus, EntryType, VersionTuple
from vdbpy.types.songs import Service, SongType, SongVersion
from vdbpy.utils.date import parse_date
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

    # disabled due to slowness (often 20s+ seconds)
    # def test_include_group_members(self) -> None:
    #     # can drift in the future
    #     _, group_song_count = get_songs_with_total_count(
    #         song_search_params=SongSearchParams(
    #             artist_ids={self.group_id}, max_results=1
    #         ),
    #     )
    #     _, group_member_song_count = get_songs_with_total_count(
    #         song_search_params=SongSearchParams(
    #             artist_ids={self.group_id}, max_results=1, include_group_members=True
    #         ),
    #     )
    #     assert group_member_song_count > group_song_count

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
        self.song_id = 1501

    def test_entry_versions(self) -> None:
        for entry_type in get_args(EntryType):
            if entry_type in {"SongList", "User"}:
                continue
            entry = get_random_entry(entry_type=entry_type)
            edits = get_edits_by_entry(entry_type, entry["id"], include_deleted=True)
            if not edits:
                logger.warning(f"No edits for {entry_type} entry {entry['id']}")
                continue
            first_edit = edits[-1]
            assert first_edit.edit_event == "Created"
            assert first_edit.entry_id == entry["id"]
            most_recent_version_id = edits[0].version_id
            most_recent_version_data = get_cached_entry_version(
                entry_type, most_recent_version_id
            )
            assert most_recent_version_data

    def test_matching_entry_and_version(self) -> None:
        edits = get_edits_by_entry("Song", self.song_id, include_deleted=True)
        version_data = get_cached_entry_version("Song", edits[0].version_id)
        assert isinstance(version_data, SongVersion)
        entry_data = get_song_by_id(
            self.song_id, fields={"pvs", "artists", "bpm", "lyrics"}
        )

        assert entry_data.length_seconds == version_data.length_seconds
        assert entry_data.original_version_id == version_data.original_version_id
        assert entry_data.publish_date == version_data.publish_date
        assert entry_data.song_type == version_data.song_type

        assert entry_data.pvs
        assert entry_data.pvs != "Unknown"
        assert {pv.pv_id for pv in entry_data.pvs} == {
            pv.pv_id for pv in version_data.pvs
        }

        version_artist_ids = {artist.artist_id for artist in version_data.artists}
        assert entry_data.artists != "Unknown"
        entry_artist_ids = {
            artist.entry.artist_id
            for artist in entry_data.artists
            if artist.entry != "Custom artist"
        }
        assert version_artist_ids == entry_artist_ids

        assert entry_data.lyrics
        assert entry_data.lyrics != "Unknown"
        assert len(entry_data.lyrics) == len(version_data.lyrics)

        assert entry_data.max_milli_bpm != "Unknown"
        assert entry_data.min_milli_bpm != "Unknown"

        assert version_data.max_milli_bpm == entry_data.max_milli_bpm
        assert version_data.min_milli_bpm == entry_data.min_milli_bpm


class TestParseData(unittest.TestCase):
    def test_parse_data(self) -> None:
        assert (
            str(parse_date("2025-09-29T04:32:04.89"))
            == "2025-09-29 04:32:04.890000+00:00"
        )
        assert str(parse_date("2025-09-29T00:00:00Z")) == "2025-09-29 00:00:00+00:00"
        assert str(parse_date("2025-09-28T12:47:09")) == "2025-09-28 12:47:09+00:00"
        assert (
            str(parse_date("2025-09-29T23:19:37.25Z"))
            == "2025-09-29 23:19:37.250000+00:00"
        )
        assert (
            str(parse_date("2025-09-28T12:46:59.327"))
            == "2025-09-28 12:46:59.327000+00:00"
        )
        assert (
            str(parse_date("2025-07-21T02:00:00+02:00")) == "2025-07-21 00:00:00+00:00"
        )
        assert str(parse_date("2025-07-21")) == "2025-07-21 00:00:00+00:00"


class TestGetEditsByDay(unittest.TestCase):
    def setUp(self) -> None:
        logger.info(f"Running test: {self._testMethodName}")
        self.EDITS_BY_DATE_SAVE_DIR = Path("edits_by_date")
        _ye = datetime.now(UTC) - timedelta(days=1)
        self.yesterday = datetime(
            year=_ye.year, month=_ye.month, day=_ye.day, tzinfo=UTC
        )

    def test_future_edit(self) -> None:
        future_edit = get_edits_by_day(
            2100, 11, 11, limit=None, save_dir=self.EDITS_BY_DATE_SAVE_DIR
        )
        assert not future_edit[0]

    def test_last_10_yesterday_edits_with_no_save_dir(self) -> None:
        ten_edits_from_yesterday, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            limit=10,
            save_dir=None,
        )
        assert len(ten_edits_from_yesterday) == 10
        assert limit_reached

    def test_yesterday_all_edits(self) -> None:
        _, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            save_dir=self.EDITS_BY_DATE_SAVE_DIR,
        )
        assert not limit_reached

    def test_last_10_yesterday_edits(self) -> None:
        ten_edits_from_yesterday, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            limit=10,
            save_dir=self.EDITS_BY_DATE_SAVE_DIR,
        )
        assert len(ten_edits_from_yesterday) == 10
        assert limit_reached

    def test_yesterday_edits_with_version_tuple_limit(self) -> None:
        ten_edits_from_yesterday, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            limit=10,
            save_dir=self.EDITS_BY_DATE_SAVE_DIR,
        )
        breakpoint_edit_index = 5
        breakpoint_edit = (
            ten_edits_from_yesterday[breakpoint_edit_index].entry_type,
            ten_edits_from_yesterday[breakpoint_edit_index].entry_id,
            ten_edits_from_yesterday[breakpoint_edit_index].version_id,
        )
        some_edits_from_yesterday, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            limit=breakpoint_edit,
            save_dir=self.EDITS_BY_DATE_SAVE_DIR,
        )
        assert len(some_edits_from_yesterday) == breakpoint_edit_index
        assert limit_reached

    def test_yesterday_edits_with_datetime_limit(self) -> None:
        all_yesterdays_edits, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            limit=self.yesterday + timedelta(hours=23),
            save_dir=self.EDITS_BY_DATE_SAVE_DIR,
        )
        logger.debug(f"Found {len(all_yesterdays_edits)} edits from yesterday")
        assert limit_reached
        assert len(all_yesterdays_edits) > 10
        for edit in all_yesterdays_edits:
            assert edit.edit_date > self.yesterday + timedelta(hours=23)

    def test_yesterday_edits_with_found_datetime_limit(self) -> None:
        all_yesterdays_edits, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            limit=self.yesterday + timedelta(hours=23),
            save_dir=self.EDITS_BY_DATE_SAVE_DIR,
        )
        mid_index = len(all_yesterdays_edits) // 2
        last_hour_date_cutoff_test = all_yesterdays_edits[mid_index].edit_date
        limited_last_hour_edits_from_yesterday, limit_reached = get_edits_by_day(
            self.yesterday.year,
            self.yesterday.month,
            self.yesterday.day,
            limit=last_hour_date_cutoff_test,
            save_dir=self.EDITS_BY_DATE_SAVE_DIR,
        )
        logger.debug(
            f"Found {len(limited_last_hour_edits_from_yesterday)} edits from yesterday"
        )
        logger.debug(f"(since {last_hour_date_cutoff_test})")
        assert len(limited_last_hour_edits_from_yesterday) < len(all_yesterdays_edits)
        assert limit_reached


class TestGetEditsByMonth(unittest.TestCase):
    def test_get_most_recent_edit_this_month(self) -> None:
        today = datetime.now(UTC)
        edits, limit_reached = get_edits_by_month(
            today.year, today.month, save_dir=Path("edits_by_date"), limit=1
        )
        assert len(edits) == 1
        assert limit_reached

    def test_get_two_edits_last_month(self) -> None:
        today = datetime.now(UTC)
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year - 1 if last_month == 12 else today.year
        edits, limit_reached = get_edits_by_month(
            last_month_year, last_month, save_dir=Path("edits_by_date"), limit=2
        )
        assert len(edits) == 2
        assert limit_reached

        edit_to_stop = (
            edits[1].entry_type,
            edits[1].entry_id,
            edits[1].version_id,
        )
        edits, limit_reached = get_edits_by_month(
            last_month_year,
            last_month,
            save_dir=Path("edits_by_date"),
            limit=edit_to_stop,
        )
        assert len(edits) == 1
        assert limit_reached


class TestGetEditsUntilDay(unittest.TestCase):
    def setUp(self) -> None:
        today = datetime.now(UTC)
        self.start_of_today = datetime(today.year, today.month, today.day, tzinfo=UTC)

    def test_get_edits_until_yesterday(self) -> None:
        edits = get_edits_until_day(
            self.start_of_today,
            save_dir=Path("edits_by_date"),
        )
        assert len(edits) > 0
        for edit in edits:
            assert edit.edit_date > self.start_of_today

    def test_get_edits_until_yesterday_with_version_tuple_limit(self) -> None:
        edits = get_edits_until_day(
            self.start_of_today, save_dir=Path("edits_by_date"), limit=2
        )
        assert len(edits) == 2

        logger.debug(f"First edit {edits[0]}")
        edit_to_stop = edits[1]
        assert edit_to_stop
        logger.debug(f"{edit_to_stop=}")

        limit: VersionTuple = (
            edit_to_stop.entry_type,
            edit_to_stop.entry_id,
            edit_to_stop.version_id,
        )
        logger.debug(f"{limit=}")
        edits = get_edits_until_day(
            self.start_of_today, save_dir=Path("edits_by_date"), limit=limit
        )
        assert 1 <= len(edits) <= 10, f"{len(edits)} edits"


class TestGetSavedEntrySearch(unittest.TestCase):
    def setUp(self) -> None:
        self.save_dir = Path("saved_entry_searches")
        self.noise_pop_tag_id = 7108  # ~ 60 song entries

    def test_noise_pop_songs(self) -> None:
        save_file = self.save_dir / "noise_pop_entries.csv"
        if Path.is_file(save_file):
            Path.unlink(save_file)

        data, counts = get_saved_entry_search(
            save_file,
            SONG_API_URL,
            {"tagId[]": self.noise_pop_tag_id},
        )
        logger.debug(f"{counts=}")
        assert counts == (0, len(data))
        assert len(set(data)) == len(data)

        entries = read_entries_from_file(save_file)
        assert len(entries) == len(data), f"{len(entries)} != {len(data)}"
        assert len(set(entries)) == len(entries)

        most_5_recent_removed = entries[5:]
        logger.debug("Saving 5 most recent removed")
        write_entries_to_file(save_file, most_5_recent_removed)

        data, counts = get_saved_entry_search(
            save_file,
            SONG_API_URL,
            {"tagId[]": self.noise_pop_tag_id, "sort": "AdditionDate"},
        )
        logger.debug(f"{counts=}")
        assert len(set(data)) == len(data)
        assert counts == (len(most_5_recent_removed), 5)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)

    unittest.main(failfast=True)

    ## Limit to certain tests only
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestGetSavedEntrySearch)
    # unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
