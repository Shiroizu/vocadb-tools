# ruff: noqa: S101
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import pytest

from vdbpy.utils.dump import get_dump_path
from vdbpy.utils.dump_sql import DumpDB, inventory_dump_keys

_EXPECTED_TABLES = {
    "songs",
    "albums",
    "artists",
    "events",
    "event_series",
    "tags",
    "entry_names",
    "entry_translated_names",
    "entry_culture_codes",
    "entry_tags",
    "entry_web_links",
    "song_artists",
    "song_pvs",
    "song_events",
    "song_albums",
    "song_lyrics",
    "song_lyric_culture_codes",
    "album_artists",
    "album_songs",
    "album_discs",
    "album_pvs",
    "album_identifiers",
    "album_events",
    "artist_groups",
    "artist_members",
    "event_artists",
    "event_pvs",
    "tag_related_tags",
    "tag_new_targets",
    "meta",
}


def _write_dump(path: Path) -> None:
    song = {
        "id": 1,
        "songType": "Original",
        "publishDate": "2020-01-01",
        "lengthSeconds": 200,
        "nicoId": "sm1",
        "minMilliBpm": 120000,
        "maxMilliBpm": 130000,
        "notes": "note",
        "notesEng": "note eng",
        "cultureCodes": ["ja"],
        "originalVersion": {"id": 2, "nameHint": "orig"},
        "releaseEvent": {"id": 10, "nameHint": "event"},
        "releaseEvents": [{"id": 11, "nameHint": "events"}],
        "names": [{"language": "English", "value": "Song"}],
        "translatedName": {
            "japanese": "曲",
            "romaji": "kyoku",
            "english": "Song",
            "default": "曲",
            "defaultLanguage": "Japanese",
        },
        "pvs": [{
            "service": "Youtube",
            "pvType": "Original",
            "pvId": "abc",
            "name": "PV",
            "author": "author",
            "description": "desc",
            "length": 200,
            "publishDate": "2020-01-01",
            "thumbUrl": "http://example.com",
            "disabled": False,
            "extendedMetadata": {"json": "{}"},
        }],
        "artists": [{"id": 3, "roles": 1, "isSupport": False, "nameHint": "P"}],
        "albums": [{"id": 4, "discNumber": 1, "trackNumber": 2, "nameHint": "Al"}],
        "lyrics": [{
            "id": 5,
            "translationType": "Original",
            "source": "source",
            "url": "http://lyrics",
            "value": "lyrics",
            "cultureCodes": ["ja"],
        }],
        "tags": [{"count": 2, "tag": {"id": 6, "nameHint": "tag"}}],
        "webLinks": [{
            "category": "Other",
            "description": "site",
            "url": "http://example.com",
            "disabled": False,
        }],
    }
    album = {
        "id": 4,
        "discType": "Album",
        "description": "album",
        "descriptionEng": "album eng",
        "mainPictureMime": "image/png",
        "names": [{"language": "English", "value": "Album"}],
        "translatedName": {
            "english": "Album",
            "japanese": "A",
            "romaji": "A",
            "defaultLanguage": "English",
        },
        "originalRelease": {
            "catNum": "ABC-1",
            "releaseDate": {"year": 2020, "month": 1, "day": 2, "isEmpty": False},
            "releaseEvent": {"id": 10, "nameHint": "release"},
            "releaseEvents": [{"id": 11, "nameHint": "releases"}],
        },
        "discs": [{"discNumber": 1, "id": 7, "mediaType": "Audio", "name": "CD"}],
        "pvs": [{
            "service": "SoundCloud",
            "pvType": "Other",
            "pvId": "sc1",
            "disabled": False,
        }],
        "artists": [{"id": 3, "roles": 1, "isSupport": True, "nameHint": "P"}],
        "songs": [{"id": 1, "discNumber": 1, "trackNumber": 2, "nameHint": "Song"}],
        "identifiers": [{"value": "JASRAC-1"}],
        "tags": [{"count": 1, "tag": {"id": 6, "nameHint": "tag"}}],
        "webLinks": [],
    }
    artist = {
        "id": 3,
        "artistType": "Producer",
        "releaseDate": "2019-01-01",
        "description": "artist",
        "descriptionEng": "artist eng",
        "cultureCodes": ["ja"],
        "baseVoicebank": {"id": 8, "nameHint": "vb"},
        "groups": [{"id": 9, "linkType": "Group", "nameHint": "circle"}],
        "members": [{"id": 10, "nameHint": "member"}],
        "names": [{"language": "English", "value": "Producer"}],
        "tags": [],
        "webLinks": [],
    }
    event = {
        "id": 10,
        "category": "AlbumRelease",
        "date": "2020-01-01",
        "series": {"id": 12, "nameHint": "series"},
        "seriesNumber": 1,
        "venue": {"id": 13, "nameHint": "venue"},
        "venueName": "Tokyo",
        "songList": {"id": 14, "nameHint": "list"},
        "description": "event",
        "name": "Event",
        "artists": [{"id": 3, "roles": 1, "nameHint": "P"}],
        "pvs": [{
            "service": "Youtube",
            "pvType": "Original",
            "pvId": "evt",
            "disabled": False,
        }],
        "names": [{"language": "English", "value": "Event"}],
        "tags": [],
        "webLinks": [],
    }
    event_series = {
        "id": 12,
        "category": "AlbumRelease",
        "description": "series",
        "aliases": ["alias"],
        "names": [{"language": "English", "value": "Series"}],
        "tags": [],
        "webLinks": [],
    }
    tag = {
        "id": 6,
        "categoryName": "Genre",
        "description": "tag",
        "descriptionEng": "tag eng",
        "hideFromSuggestions": True,
        "targets": 3,
        "thumbMime": "image/png",
        "parent": {"id": 15, "nameHint": "parent"},
        "relatedTags": [{"id": 16, "nameHint": "related"}],
        "newTargets": ["Song"],
        "names": [{"language": "English", "value": "Tag"}],
        "webLinks": [],
    }

    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Songs/1.json", json.dumps([song]))
        z.writestr("Albums/1.json", json.dumps([album]))
        z.writestr("Artists/1.json", json.dumps([artist]))
        z.writestr("Events/1.json", json.dumps([event]))
        z.writestr("EventSeries/1.json", json.dumps([event_series]))
        z.writestr("Tags/1.json", json.dumps([tag]))


def test_build_creates_full_mirror_schema() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dump_path = Path(tmp) / "dump.zip"
        _write_dump(dump_path)
        db = DumpDB.build(dump_path)

        conn = sqlite3.connect(db.path)
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'",
                ).fetchall()
            }
            assert _EXPECTED_TABLES.issubset(tables)

            assert conn.execute("SELECT count(*) FROM song_pvs").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM song_lyrics").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM album_discs").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM artist_groups").fetchone()[0] == 1
            members = conn.execute(
                "SELECT count(*) FROM artist_members",
            ).fetchone()[0]
            assert members == 1
            event_pvs = conn.execute("SELECT count(*) FROM event_pvs").fetchone()[0]
            assert event_pvs == 1
            related = conn.execute(
                "SELECT count(*) FROM tag_related_tags",
            ).fetchone()[0]
            assert related == 1
            tag_hint = conn.execute(
                "SELECT tag_name_hint FROM entry_tags LIMIT 1",
            ).fetchone()[0]
            assert tag_hint == "tag"
        finally:
            conn.close()


def test_inventory_dump_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dump_path = Path(tmp) / "dump.zip"
        _write_dump(dump_path)
        keys = inventory_dump_keys(dump_path)
        assert "cultureCodes" in keys["Songs"]
        assert "groups" in keys["Artists"]
        assert "relatedTags" in keys["Tags"]


@pytest.mark.slow
def test_real_dump_inventory_has_no_unmapped_top_level_keys() -> None:
    mapped = {
        "Albums": {
            "artists", "description", "descriptionEng", "discType", "discs", "id",
            "identifiers", "mainPictureMime", "names", "originalRelease", "pictures",
            "pvs", "songs", "tags", "translatedName", "webLinks",
        },
        "Artists": {
            "artistType", "baseVoicebank", "cultureCodes", "description",
            "descriptionEng", "groups", "id", "mainPictureMime", "members", "names",
            "pictures", "releaseDate", "tags", "translatedName", "webLinks",
        },
        "EventSeries": {
            "aliases", "category", "description", "id", "mainPictureMime", "names",
            "tags", "translatedName", "webLinks",
        },
        "Events": {
            "artists", "category", "date", "description", "id", "mainPictureMime",
            "name", "names", "pvs", "series", "seriesNumber", "songList", "tags",
            "translatedName", "venue", "venueName", "webLinks",
        },
        "Songs": {
            "albums", "artists", "cultureCodes", "id", "lengthSeconds", "lyrics",
            "maxMilliBpm", "minMilliBpm", "names", "nicoId", "notes", "notesEng",
            "originalVersion", "publishDate", "pvs", "releaseEvent", "releaseEvents",
            "songType", "tags", "translatedName", "webLinks",
        },
        "Tags": {
            "categoryName", "description", "descriptionEng", "hideFromSuggestions",
            "id", "names", "newTargets", "parent", "relatedTags", "targets",
            "thumbMime", "translatedName", "webLinks",
        },
    }
    keys = inventory_dump_keys(get_dump_path())
    for folder, expected in mapped.items():
        assert keys[folder].issubset(expected | keys[folder])
        unknown = keys[folder] - expected
        assert not unknown, f"Unmapped keys in {folder}: {sorted(unknown)}"
