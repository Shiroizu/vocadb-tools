"""SQLite preprocessing of the VocaDB data dump."""

from __future__ import annotations

import sqlite3
import time
import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

import orjson
from sqlalchemy import Row, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from vdbpy.utils.dump import get_dump_path
from vdbpy.utils.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from pathlib import Path

    from sqlalchemy import Engine
    from sqlalchemy.sql import Select

_Row = TypeVar("_Row", bound=tuple)
_T = TypeVar("_T")

logger = get_logger()

_READONLY_ACTIONS = frozenset({
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
})


class SqlError(Exception):
    """Raised when an ad-hoc SQL query is rejected or fails."""


@dataclass
class SqlResult:
    columns: list[str]
    rows: list[tuple]
    truncated: bool


class Base(DeclarativeBase):
    pass


# -------- main tables -------- #


class Song(Base):
    __tablename__ = "songs"
    id: Mapped[int] = mapped_column(primary_key=True)
    song_type: Mapped[str]
    publish_date: Mapped[str | None]
    length_seconds: Mapped[int | None]
    original_id: Mapped[int | None]
    nico_id: Mapped[str | None]
    min_milli_bpm: Mapped[int | None]
    max_milli_bpm: Mapped[int | None]
    notes: Mapped[str | None]
    notes_eng: Mapped[str | None]
    name_en: Mapped[str | None]


class Album(Base):
    __tablename__ = "albums"
    id: Mapped[int] = mapped_column(primary_key=True)
    disc_type: Mapped[str]
    description: Mapped[str | None]
    description_eng: Mapped[str | None]
    cat_num: Mapped[str | None]
    release_year: Mapped[int | None]
    release_month: Mapped[int | None]
    release_day: Mapped[int | None]
    release_is_empty: Mapped[int | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class Artist(Base):
    __tablename__ = "artists"
    id: Mapped[int] = mapped_column(primary_key=True)
    artist_type: Mapped[str]
    base_voicebank_id: Mapped[int | None]
    release_date: Mapped[str | None]
    description: Mapped[str | None]
    description_eng: Mapped[str | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str]
    date: Mapped[str | None]
    series_id: Mapped[int | None]
    series_number: Mapped[int | None]
    venue_id: Mapped[int | None]
    venue_name: Mapped[str | None]
    song_list_id: Mapped[int | None]
    description: Mapped[str | None]
    name: Mapped[str | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class EventSeries(Base):
    __tablename__ = "event_series"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str]
    description: Mapped[str | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str]
    parent_id: Mapped[int | None]
    description: Mapped[str | None]
    description_eng: Mapped[str | None]
    hide_from_suggestions: Mapped[int]
    targets: Mapped[int | None]
    thumb_mime: Mapped[str | None]
    name_en: Mapped[str | None]


# -------- shared tables -------- #


class EntryName(Base):
    __tablename__ = "entry_names"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    language: Mapped[str]
    value: Mapped[str]


class EntryTranslatedName(Base):
    __tablename__ = "entry_translated_names"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    japanese: Mapped[str | None]
    romaji: Mapped[str | None]
    english: Mapped[str | None]
    default_name: Mapped[str | None]
    default_language: Mapped[str | None]


class EntryCultureCode(Base):
    __tablename__ = "entry_culture_codes"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    code: Mapped[str]


class EntryTag(Base):
    __tablename__ = "entry_tags"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    tag_id: Mapped[int]
    count: Mapped[int]
    tag_name_hint: Mapped[str | None]


class EntryWebLink(Base):
    __tablename__ = "entry_web_links"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    category: Mapped[str]
    description: Mapped[str]
    url: Mapped[str]
    disabled: Mapped[int]


# -------- per-entity helper tables -------- #


class SongArtist(Base):
    __tablename__ = "song_artists"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    artist_id: Mapped[int]
    roles: Mapped[int]
    is_support: Mapped[int]
    name_hint: Mapped[str | None]


class SongPV(Base):
    __tablename__ = "song_pvs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    service: Mapped[str]
    pv_type: Mapped[str]
    pv_id: Mapped[str]
    name: Mapped[str | None]
    author: Mapped[str | None]
    description: Mapped[str | None]
    length: Mapped[int | None]
    publish_date: Mapped[str | None]
    thumb_url: Mapped[str | None]
    disabled: Mapped[int]
    extended_metadata_json: Mapped[str | None]


class SongEvent(Base):
    __tablename__ = "song_events"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    event_id: Mapped[int]
    name_hint: Mapped[str | None]


class SongAlbum(Base):
    __tablename__ = "song_albums"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    album_id: Mapped[int]
    disc_number: Mapped[int | None]
    track_number: Mapped[int | None]
    name_hint: Mapped[str | None]


class AlbumArtist(Base):
    __tablename__ = "album_artists"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    artist_id: Mapped[int]
    roles: Mapped[int]
    is_support: Mapped[int]
    name_hint: Mapped[str | None]


class AlbumSong(Base):
    __tablename__ = "album_songs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    song_id: Mapped[int]
    disc_number: Mapped[int | None]
    track_number: Mapped[int | None]
    name_hint: Mapped[str | None]


class AlbumDisc(Base):
    __tablename__ = "album_discs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    disc_number: Mapped[int | None]
    disc_id: Mapped[int | None]
    media_type: Mapped[str | None]
    name: Mapped[str | None]


class AlbumPV(Base):
    __tablename__ = "album_pvs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    service: Mapped[str]
    pv_type: Mapped[str]
    pv_id: Mapped[str]
    name: Mapped[str | None]
    author: Mapped[str | None]
    description: Mapped[str | None]
    length: Mapped[int | None]
    publish_date: Mapped[str | None]
    thumb_url: Mapped[str | None]
    disabled: Mapped[int]
    extended_metadata_json: Mapped[str | None]


class AlbumIdentifier(Base):
    __tablename__ = "album_identifiers"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    value: Mapped[str]


class AlbumEvent(Base):
    __tablename__ = "album_events"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    event_id: Mapped[int]
    name_hint: Mapped[str | None]


class ArtistGroup(Base):
    __tablename__ = "artist_groups"
    pk: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[int]
    linked_artist_id: Mapped[int]
    link_type: Mapped[str]
    name_hint: Mapped[str | None]


class ArtistMember(Base):
    __tablename__ = "artist_members"
    pk: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[int]
    member_artist_id: Mapped[int]
    name_hint: Mapped[str | None]


class EventArtist(Base):
    __tablename__ = "event_artists"
    pk: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int]
    artist_id: Mapped[int]
    roles: Mapped[int]
    is_support: Mapped[int]
    name_hint: Mapped[str | None]


class EventPV(Base):
    __tablename__ = "event_pvs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int]
    service: Mapped[str]
    pv_type: Mapped[str]
    pv_id: Mapped[str]
    name: Mapped[str | None]
    author: Mapped[str | None]
    description: Mapped[str | None]
    length: Mapped[int | None]
    publish_date: Mapped[str | None]
    thumb_url: Mapped[str | None]
    disabled: Mapped[int]
    extended_metadata_json: Mapped[str | None]


class TagRelatedTag(Base):
    __tablename__ = "tag_related_tags"
    pk: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[int]
    related_tag_id: Mapped[int]
    name_hint: Mapped[str | None]


class TagNewTarget(Base):
    __tablename__ = "tag_new_targets"
    pk: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[int]
    target: Mapped[str]


class Meta(Base):
    __tablename__ = "meta"
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]


# -------- dump helpers -------- #


def _iter_raw(dump_path: Path, folder: str) -> Iterator[dict]:
    with zipfile.ZipFile(dump_path) as z:
        for name in sorted(z.namelist()):
            if name.startswith(f"{folder}/") and name.endswith(".json"):
                try:
                    yield from orjson.loads(z.read(name))
                except orjson.JSONDecodeError:
                    logger.warning("dump_sql: skipping corrupt chunk %s", name)


def inventory_dump_keys(dump_path: Path) -> dict[str, set[str]]:
    """Return top-level JSON keys seen per dump folder."""
    keys: dict[str, set[str]] = {}
    with zipfile.ZipFile(dump_path) as z:
        for name in sorted(z.namelist()):
            if not name.endswith(".json"):
                continue
            folder = name.split("/")[0]
            try:
                entries = orjson.loads(z.read(name))
            except orjson.JSONDecodeError:
                continue
            bucket = keys.setdefault(folder, set())
            for entry in entries:
                bucket.update(entry.keys())
    return keys


def _ref_id(key: str) -> Callable[[dict], object]:
    return lambda e: (e.get(key) or {}).get("id")


def _name_en(e: dict) -> str | None:
    for n in e.get("names") or []:
        if n.get("language") == "English" and (n.get("value") or "").strip():
            return n["value"]
    return None


def _album_release(
    e: dict,
) -> tuple[str | None, int | None, int | None, int | None, int]:
    rel = (e.get("originalRelease") or {}).get("releaseDate") or {}
    year = rel.get("year")
    month = rel.get("month")
    day = rel.get("day")
    is_empty = int(bool(rel.get("isEmpty", True)))
    if is_empty or not year:
        return None, year, month, day, is_empty
    return (
        f"{year:04d}-{(month or 0):02d}-{(day or 0):02d}",
        year,
        month,
        day,
        is_empty,
    )


def _name_rows(entry_type: str, e: dict) -> Iterator[tuple[str, int, str, str]]:
    eid = e["id"]
    for n in e.get("names") or []:
        yield (entry_type, eid, n.get("language", "Unspecified"), n.get("value", ""))
    for alias in e.get("aliases") or []:
        yield (entry_type, eid, "Alias", alias)


def _translated_name_row(entry_type: str, e: dict) -> tuple | None:
    tn = e.get("translatedName")
    if not tn:
        return None
    return (
        entry_type,
        e["id"],
        tn.get("japanese") or None,
        tn.get("romaji") or None,
        tn.get("english") or None,
        tn.get("default") or None,
        tn.get("defaultLanguage") or None,
    )


def _culture_code_rows(entry_type: str, e: dict) -> Iterator[tuple[str, int, str]]:
    eid = e["id"]
    for code in e.get("cultureCodes") or []:
        yield (entry_type, eid, code)


def _tag_rows(
    entry_type: str,
    e: dict,
) -> Iterator[tuple[str, int, int, int, str | None]]:
    eid = e["id"]
    for usage in e.get("tags") or []:
        tag = usage.get("tag")
        if tag:
            yield (
                entry_type,
                eid,
                tag["id"],
                usage.get("count", 0),
                tag.get("nameHint") or None,
            )


def _weblink_rows(
    entry_type: str,
    e: dict,
) -> Iterator[tuple[str, int, str, str, str, int]]:
    eid = e["id"]
    for w in e.get("webLinks") or []:
        yield (
            entry_type,
            eid,
            w.get("category", ""),
            w.get("description", ""),
            w.get("url", ""),
            int(bool(w.get("disabled"))),
        )


def _credit_rows(
    parent_id: int,
    artists: list | None,
) -> Iterator[tuple[int, int, int, int, str | None]]:
    for a in artists or []:
        yield (
            parent_id,
            a["id"],
            a.get("roles", 0),
            int(bool(a.get("isSupport"))),
            a.get("nameHint") or None,
        )


def _ref_rows(
    parent_id: int,
    items: list | None,
) -> Iterator[tuple[int, int, str | None]]:
    for item in items or []:
        if isinstance(item, dict):
            item_id = item.get("id")
            name_hint = item.get("nameHint") or None
        else:
            item_id = item
            name_hint = None
        if item_id is not None:
            yield (parent_id, item_id, name_hint)


def _pv_metadata_json(pv: dict) -> str | None:
    meta = pv.get("extendedMetadata")
    if not meta:
        return None
    return orjson.dumps(meta).decode()


def _pv_rows(parent_id: int, pvs: list | None) -> Iterator[tuple]:
    for pv in pvs or []:
        yield (
            parent_id,
            pv.get("service", ""),
            pv.get("pvType", ""),
            pv.get("pvId", ""),
            pv.get("name") or None,
            pv.get("author") or None,
            pv.get("description") or None,
            pv.get("length"),
            pv.get("publishDate"),
            pv.get("thumbUrl") or None,
            int(bool(pv.get("disabled"))),
            _pv_metadata_json(pv),
        )


@dataclass
class _Col:
    name: str
    extract: Callable[[dict], object]


@dataclass
class _EntitySpec:
    folder: str
    table: str
    entry_type: str
    columns: list[_Col]


_ENTITY_SPECS: list[_EntitySpec] = [
    _EntitySpec(
        "Songs", "songs", "Song",
        columns=[
            _Col("id", lambda e: e["id"]),
            _Col("song_type", lambda e: e.get("songType", "Unspecified")),
            _Col("publish_date", lambda e: e.get("publishDate")),
            _Col("length_seconds", lambda e: e.get("lengthSeconds")),
            _Col("original_id", _ref_id("originalVersion")),
            _Col("nico_id", lambda e: e.get("nicoId") or None),
            _Col("min_milli_bpm", lambda e: e.get("minMilliBpm")),
            _Col("max_milli_bpm", lambda e: e.get("maxMilliBpm")),
            _Col("notes", lambda e: e.get("notes") or None),
            _Col("notes_eng", lambda e: e.get("notesEng") or None),
            _Col("name_en", _name_en),
        ],
    ),
    _EntitySpec(
        "Albums", "albums", "Album",
        columns=[
            _Col("id", lambda e: e["id"]),
            _Col("disc_type", lambda e: e.get("discType", "Unknown")),
            _Col("description", lambda e: e.get("description") or None),
            _Col("description_eng", lambda e: e.get("descriptionEng") or None),
            _Col(
                "cat_num",
                lambda e: (e.get("originalRelease") or {}).get("catNum") or None,
            ),
            _Col("release_year", lambda e: _album_release(e)[1]),
            _Col("release_month", lambda e: _album_release(e)[2]),
            _Col("release_day", lambda e: _album_release(e)[3]),
            _Col("release_is_empty", lambda e: _album_release(e)[4]),
            _Col("main_picture_mime", lambda e: e.get("mainPictureMime") or None),
            _Col("name_en", _name_en),
        ],
    ),
    _EntitySpec(
        "Artists", "artists", "Artist",
        columns=[
            _Col("id", lambda e: e["id"]),
            _Col("artist_type", lambda e: e.get("artistType", "Unknown")),
            _Col("base_voicebank_id", _ref_id("baseVoicebank")),
            _Col("release_date", lambda e: e.get("releaseDate") or None),
            _Col("description", lambda e: e.get("description") or None),
            _Col("description_eng", lambda e: e.get("descriptionEng") or None),
            _Col("main_picture_mime", lambda e: e.get("mainPictureMime") or None),
            _Col("name_en", _name_en),
        ],
    ),
    _EntitySpec(
        "Events", "events", "ReleaseEvent",
        columns=[
            _Col("id", lambda e: e["id"]),
            _Col("category", lambda e: e.get("category", "Unspecified")),
            _Col("date", lambda e: e.get("date") or None),
            _Col("series_id", _ref_id("series")),
            _Col("series_number", lambda e: e.get("seriesNumber")),
            _Col("venue_id", _ref_id("venue")),
            _Col("venue_name", lambda e: e.get("venueName") or None),
            _Col("song_list_id", _ref_id("songList")),
            _Col("description", lambda e: e.get("description") or None),
            _Col("name", lambda e: e.get("name") or None),
            _Col("main_picture_mime", lambda e: e.get("mainPictureMime") or None),
            _Col("name_en", _name_en),
        ],
    ),
    _EntitySpec(
        "EventSeries", "event_series", "ReleaseEventSeries",
        columns=[
            _Col("id", lambda e: e["id"]),
            _Col("category", lambda e: e.get("category", "Unspecified")),
            _Col("description", lambda e: e.get("description") or None),
            _Col("main_picture_mime", lambda e: e.get("mainPictureMime") or None),
            _Col("name_en", _name_en),
        ],
    ),
    _EntitySpec(
        "Tags", "tags", "Tag",
        columns=[
            _Col("id", lambda e: e["id"]),
            _Col("category_name", lambda e: e.get("categoryName") or ""),
            _Col("parent_id", _ref_id("parent")),
            _Col("description", lambda e: e.get("description") or None),
            _Col("description_eng", lambda e: e.get("descriptionEng") or None),
            _Col(
                "hide_from_suggestions",
                lambda e: int(bool(e.get("hideFromSuggestions"))),
            ),
            _Col("targets", lambda e: e.get("targets")),
            _Col("thumb_mime", lambda e: e.get("thumbMime") or None),
            _Col("name_en", _name_en),
        ],
    ),
]

_TABLE_ORDER: dict[str, int] = {
    "songs": 0,
    "albums": 1,
    "artists": 2,
    "events": 3,
    "event_series": 4,
    "tags": 5,
    "song_artists": 10,
    "song_pvs": 11,
    "song_events": 12,
    "song_albums": 13,
    "album_artists": 16,
    "album_songs": 17,
    "album_discs": 18,
    "album_pvs": 19,
    "album_identifiers": 20,
    "album_events": 21,
    "artist_groups": 22,
    "artist_members": 23,
    "event_artists": 24,
    "event_pvs": 25,
    "tag_related_tags": 26,
    "tag_new_targets": 27,
    "entry_names": 30,
    "entry_translated_names": 31,
    "entry_culture_codes": 32,
    "entry_tags": 33,
    "entry_web_links": 34,
    "meta": 40,
}


def _format_columns(columns: list[tuple]) -> str:
    names = [
        f"{name} (pk)" if pk else name
        for _cid, name, _col_type, _notnull, _default, pk in columns
    ]
    return ", ".join(names)


def _format_indexes(conn: Any, table: str) -> str | None:
    indexes: list[str] = []
    for _seq, name, unique, origin, _partial in conn.exec_driver_sql(
        f'PRAGMA index_list("{table}")',
    ).all():
        if origin == "pk":
            continue
        columns = [
            row[2]
            for row in conn.exec_driver_sql(f'PRAGMA index_info("{name}")').all()
        ]
        if columns:
            prefix = "unique " if unique else ""
            indexes.append(f"{prefix}{', '.join(columns)}")
    return "; ".join(indexes) if indexes else None


def _format_schema(conn: Any) -> str:
    table_names = [
        row[0]
        for row in conn.exec_driver_sql(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        ).all()
    ]
    table_names.sort(key=lambda name: (_TABLE_ORDER.get(name, 50), name))

    parts: list[str] = []
    for table in table_names:
        columns = conn.exec_driver_sql(f'PRAGMA table_info("{table}")').all()
        lines = [table, f"  columns: {_format_columns(columns)}"]
        indexes = _format_indexes(conn, table)
        if indexes:
            lines.append(f"  indexes: {indexes}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


class DumpDB:
    Song = Song
    Album = Album
    Artist = Artist
    Event = Event
    EventSeries = EventSeries
    Tag = Tag
    EntryName = EntryName
    EntryTag = EntryTag
    SongArtist = SongArtist
    SongPV = SongPV
    SongEvent = SongEvent
    AlbumEvent = AlbumEvent
    ArtistGroup = ArtistGroup
    ArtistMember = ArtistMember

    def __init__(self, engine: Engine, path: Path) -> None:
        self.engine = engine
        self.path = path

    @classmethod
    def build(cls, dump_path: Path | None = None) -> DumpDB:
        if dump_path is None:
            dump_path = get_dump_path()
        db_path = dump_path.parent / "dump.sqlite"
        dump_mtime = str(dump_path.stat().st_mtime)

        if db_path.exists():
            engine = create_engine(f"sqlite:///{db_path}")
            if cls._stored_mtime(engine) == dump_mtime:
                logger.info("Loaded preprocessed dump database from cache.")
                return cls(engine, db_path)
            engine.dispose()
            db_path.unlink()

        logger.info("Building preprocessed dump database...")
        start = time.monotonic()
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        cls._ingest(engine, dump_path, dump_mtime)
        logger.info(f"Built dump database in {time.monotonic() - start:.1f}s.")
        return cls(engine, db_path)

    @staticmethod
    def _stored_mtime(engine: Engine) -> str | None:
        try:
            with engine.connect() as conn:
                row = conn.execute(
                    select(Meta.value).where(Meta.key == "dump_mtime"),
                ).first()
        except Exception:  # noqa: BLE001
            return None
        return row[0] if row else None

    @staticmethod
    def _ingest(engine: Engine, dump_path: Path, dump_mtime: str) -> None:
        raw = engine.raw_connection()
        try:
            cur = raw.cursor()
            cur.execute("PRAGMA journal_mode=OFF")
            cur.execute("PRAGMA synchronous=OFF")

            buffers: dict[str, list] = {
                "entry_names": [],
                "entry_translated_names": [],
                "entry_culture_codes": [],
                "entry_tags": [],
                "entry_web_links": [],
                "song_artists": [],
                "song_pvs": [],
                "song_events": [],
                "song_albums": [],
                "album_artists": [],
                "album_songs": [],
                "album_discs": [],
                "album_pvs": [],
                "album_identifiers": [],
                "album_events": [],
                "artist_groups": [],
                "artist_members": [],
                "event_artists": [],
                "event_pvs": [],
                "tag_related_tags": [],
                "tag_new_targets": [],
            }

            def _song_children(e: dict) -> None:
                buffers["song_artists"].extend(_credit_rows(e["id"], e.get("artists")))
                buffers["song_pvs"].extend(_pv_rows(e["id"], e.get("pvs")))
                for _, event_id, name_hint in _ref_rows(
                    e["id"], e.get("releaseEvents"),
                ):
                    buffers["song_events"].append((e["id"], event_id, name_hint))
                release_event = e.get("releaseEvent")
                if (
                    isinstance(release_event, dict)
                    and release_event.get("id") is not None
                ):
                    buffers["song_events"].append((
                        e["id"],
                        release_event["id"],
                        release_event.get("nameHint") or None,
                    ))
                for album in e.get("albums") or []:
                    buffers["song_albums"].append((
                        e["id"],
                        album["id"],
                        album.get("discNumber"),
                        album.get("trackNumber"),
                        album.get("nameHint") or None,
                    ))

            def _album_children(e: dict) -> None:
                buffers["album_artists"].extend(_credit_rows(e["id"], e.get("artists")))
                for track in e.get("songs") or []:
                    buffers["album_songs"].append((
                        e["id"],
                        track["id"],
                        track.get("discNumber"),
                        track.get("trackNumber"),
                        track.get("nameHint") or None,
                    ))
                for disc in e.get("discs") or []:
                    buffers["album_discs"].append((
                        e["id"],
                        disc.get("discNumber"),
                        disc.get("id"),
                        disc.get("mediaType") or None,
                        disc.get("name") or None,
                    ))
                buffers["album_pvs"].extend(_pv_rows(e["id"], e.get("pvs")))
                for ident in e.get("identifiers") or []:
                    value = ident["value"] if isinstance(ident, dict) else str(ident)
                    buffers["album_identifiers"].append((e["id"], value))
                rel = e.get("originalRelease") or {}
                for _, event_id, name_hint in _ref_rows(
                    e["id"], rel.get("releaseEvents"),
                ):
                    buffers["album_events"].append((e["id"], event_id, name_hint))
                release_event = rel.get("releaseEvent")
                if (
                    isinstance(release_event, dict)
                    and release_event.get("id") is not None
                ):
                    buffers["album_events"].append((
                        e["id"],
                        release_event["id"],
                        release_event.get("nameHint") or None,
                    ))

            def _artist_children(e: dict) -> None:
                for group in e.get("groups") or []:
                    if group.get("id") is not None:
                        buffers["artist_groups"].append((
                            e["id"],
                            group["id"],
                            group.get("linkType", ""),
                            group.get("nameHint") or None,
                        ))
                for member in e.get("members") or []:
                    if member.get("id") is not None:
                        buffers["artist_members"].append((
                            e["id"],
                            member["id"],
                            member.get("nameHint") or None,
                        ))

            def _event_children(e: dict) -> None:
                buffers["event_artists"].extend(_credit_rows(e["id"], e.get("artists")))
                buffers["event_pvs"].extend(_pv_rows(e["id"], e.get("pvs")))

            def _tag_children(e: dict) -> None:
                for related in e.get("relatedTags") or []:
                    if related.get("id") is not None:
                        buffers["tag_related_tags"].append((
                            e["id"],
                            related["id"],
                            related.get("nameHint") or None,
                        ))
                for target in e.get("newTargets") or []:
                    buffers["tag_new_targets"].append((e["id"], target))

            child_cbs: dict[str, Callable[[dict], None]] = {
                "Songs": _song_children,
                "Albums": _album_children,
                "Artists": _artist_children,
                "Events": _event_children,
                "Tags": _tag_children,
            }

            for spec in _ENTITY_SPECS:
                _ingest_entity(
                    cur,
                    dump_path,
                    spec,
                    buffers,
                    child_cbs.get(spec.folder),
                )

            _bulk_insert(cur, "entry_names",
                         "entry_type,entry_id,language,value",
                         buffers["entry_names"])
            _bulk_insert(cur, "entry_translated_names",
                         "entry_type,entry_id,japanese,romaji,english,default_name,default_language",
                         buffers["entry_translated_names"])
            _bulk_insert(cur, "entry_culture_codes",
                         "entry_type,entry_id,code",
                         buffers["entry_culture_codes"])
            _bulk_insert(cur, "entry_tags",
                         "entry_type,entry_id,tag_id,count,tag_name_hint",
                         buffers["entry_tags"])
            _bulk_insert(cur, "entry_web_links",
                         "entry_type,entry_id,category,description,url,disabled",
                         buffers["entry_web_links"])
            _bulk_insert(cur, "song_artists",
                         "song_id,artist_id,roles,is_support,name_hint",
                         buffers["song_artists"])
            _bulk_insert(cur, "song_pvs",
                         "song_id,service,pv_type,pv_id,name,author,description,"
                         "length,publish_date,thumb_url,disabled,extended_metadata_json",
                         buffers["song_pvs"])
            _bulk_insert(cur, "song_events",
                         "song_id,event_id,name_hint",
                         buffers["song_events"])
            _bulk_insert(cur, "song_albums",
                         "song_id,album_id,disc_number,track_number,name_hint",
                         buffers["song_albums"])
            _bulk_insert(cur, "album_artists",
                         "album_id,artist_id,roles,is_support,name_hint",
                         buffers["album_artists"])
            _bulk_insert(cur, "album_songs",
                         "album_id,song_id,disc_number,track_number,name_hint",
                         buffers["album_songs"])
            _bulk_insert(cur, "album_discs",
                         "album_id,disc_number,disc_id,media_type,name",
                         buffers["album_discs"])
            _bulk_insert(cur, "album_pvs",
                         "album_id,service,pv_type,pv_id,name,author,description,"
                         "length,publish_date,thumb_url,disabled,extended_metadata_json",
                         buffers["album_pvs"])
            _bulk_insert(cur, "album_identifiers",
                         "album_id,value",
                         buffers["album_identifiers"])
            _bulk_insert(cur, "album_events",
                         "album_id,event_id,name_hint",
                         buffers["album_events"])
            _bulk_insert(cur, "artist_groups",
                         "artist_id,linked_artist_id,link_type,name_hint",
                         buffers["artist_groups"])
            _bulk_insert(cur, "artist_members",
                         "artist_id,member_artist_id,name_hint",
                         buffers["artist_members"])
            _bulk_insert(cur, "event_artists",
                         "event_id,artist_id,roles,is_support,name_hint",
                         buffers["event_artists"])
            _bulk_insert(cur, "event_pvs",
                         "event_id,service,pv_type,pv_id,name,author,description,"
                         "length,publish_date,thumb_url,disabled,extended_metadata_json",
                         buffers["event_pvs"])
            _bulk_insert(cur, "tag_related_tags",
                         "tag_id,related_tag_id,name_hint",
                         buffers["tag_related_tags"])
            _bulk_insert(cur, "tag_new_targets",
                         "tag_id,target",
                         buffers["tag_new_targets"])

            _create_indexes(cur)
            cur.execute(
                "INSERT INTO meta(key,value) VALUES('dump_mtime',?)", (dump_mtime,))
            raw.commit()
        finally:
            raw.close()

    def exec(self, stmt: Select[_Row]) -> Sequence[Row[_Row]]:
        with self.engine.connect() as conn:
            return conn.execute(stmt).all()

    def scalars(self, stmt: Select[tuple[_T]]) -> list[_T]:
        with self.engine.connect() as conn:
            return list(conn.scalars(stmt).all())

    def schema_sql(self) -> str:
        with self.engine.connect() as conn:
            return _format_schema(conn)

    def run_readonly_select(
        self,
        sql: str,
        *,
        max_rows: int = 100,
        timeout_s: float = 5.0,
    ) -> SqlResult:
        statement = sql.strip().rstrip(";").strip()
        if not statement:
            raise SqlError("Empty query.")
        if not statement.lower().startswith(("select", "with")):
            raise SqlError("Only SELECT queries are allowed.")

        conn = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
        deadline = time.monotonic() + timeout_s
        try:
            conn.set_authorizer(_readonly_authorizer)
            conn.set_progress_handler(
                lambda: int(time.monotonic() > deadline), 10_000,
            )
            try:
                cursor = conn.execute(statement)
                description = cursor.description
                fetched = cursor.fetchmany(max_rows + 1)
            except sqlite3.OperationalError as exc:
                if time.monotonic() > deadline:
                    raise SqlError(f"Query exceeded {timeout_s:g}s timeout.") from exc
                raise SqlError(f"Query error: {exc}") from exc
            except (sqlite3.ProgrammingError, sqlite3.DatabaseError) as exc:
                raise SqlError(f"Query rejected: {exc}") from exc
        finally:
            conn.close()

        columns = [col[0] for col in description] if description else []
        return SqlResult(
            columns=columns,
            rows=[tuple(row) for row in fetched[:max_rows]],
            truncated=len(fetched) > max_rows,
        )


def _readonly_authorizer(action: int, *_args: object) -> int:
    return sqlite3.SQLITE_OK if action in _READONLY_ACTIONS else sqlite3.SQLITE_DENY


def _bulk_insert(cur: Any, table: str, columns: str, rows: list) -> None:
    if not rows:
        return
    placeholders = ",".join("?" * len(columns.split(",")))
    cur.executemany(
        f"INSERT INTO {table}({columns}) VALUES({placeholders})",
        rows,
    )


def _ingest_entity(
    cur: Any,
    dump_path: Path,
    spec: _EntitySpec,
    buffers: dict[str, list],
    child_cb: Callable[[dict], None] | None,
) -> None:
    column_names = [col.name for col in spec.columns]
    placeholders = ",".join("?" * len(column_names))
    rows: list[tuple] = []
    for e in _iter_raw(dump_path, spec.folder):
        rows.append(tuple(col.extract(e) for col in spec.columns))
        buffers["entry_names"].extend(_name_rows(spec.entry_type, e))
        tn = _translated_name_row(spec.entry_type, e)
        if tn is not None:
            buffers["entry_translated_names"].append(tn)
        buffers["entry_culture_codes"].extend(_culture_code_rows(spec.entry_type, e))
        buffers["entry_tags"].extend(_tag_rows(spec.entry_type, e))
        buffers["entry_web_links"].extend(_weblink_rows(spec.entry_type, e))
        if child_cb is not None:
            child_cb(e)
    cur.executemany(
        f"INSERT INTO {spec.table}({','.join(column_names)}) "
        f"VALUES({placeholders})",
        rows,
    )


def _create_indexes(cur: Any) -> None:
    statements = (
        "CREATE INDEX ix_names_entry ON entry_names(entry_type,entry_id)",
        "CREATE INDEX ix_translated_names_entry "
        "ON entry_translated_names(entry_type,entry_id)",
        "CREATE INDEX ix_culture_codes_entry "
        "ON entry_culture_codes(entry_type,entry_id)",
        "CREATE INDEX ix_tags_entry ON entry_tags(entry_type,entry_id)",
        "CREATE INDEX ix_tags_tag ON entry_tags(tag_id)",
        "CREATE INDEX ix_weblinks_entry ON entry_web_links(entry_type,entry_id)",
        "CREATE INDEX ix_songs_orig ON songs(original_id)",
        "CREATE INDEX ix_sa_song ON song_artists(song_id)",
        "CREATE INDEX ix_sa_artist ON song_artists(artist_id)",
        "CREATE INDEX ix_song_pvs_song ON song_pvs(song_id)",
        "CREATE INDEX ix_song_events_song ON song_events(song_id)",
        "CREATE INDEX ix_song_events_event ON song_events(event_id)",
        "CREATE INDEX ix_song_albums_song ON song_albums(song_id)",
        "CREATE INDEX ix_song_albums_album ON song_albums(album_id)",
        "CREATE INDEX ix_album_artists ON album_artists(album_id)",
        "CREATE INDEX ix_album_artists_artist ON album_artists(artist_id)",
        "CREATE INDEX ix_album_songs ON album_songs(album_id)",
        "CREATE INDEX ix_album_songs_song ON album_songs(song_id)",
        "CREATE INDEX ix_album_discs ON album_discs(album_id)",
        "CREATE INDEX ix_album_pvs ON album_pvs(album_id)",
        "CREATE INDEX ix_album_idents ON album_identifiers(album_id)",
        "CREATE INDEX ix_album_events_album ON album_events(album_id)",
        "CREATE INDEX ix_album_events_event ON album_events(event_id)",
        "CREATE INDEX ix_artist_groups_artist ON artist_groups(artist_id)",
        "CREATE INDEX ix_artist_groups_linked ON artist_groups(linked_artist_id)",
        "CREATE INDEX ix_artist_members_artist ON artist_members(artist_id)",
        "CREATE INDEX ix_artist_members_member ON artist_members(member_artist_id)",
        "CREATE INDEX ix_event_artists ON event_artists(event_id)",
        "CREATE INDEX ix_event_artists_artist ON event_artists(artist_id)",
        "CREATE INDEX ix_event_pvs ON event_pvs(event_id)",
        "CREATE INDEX ix_tag_related ON tag_related_tags(tag_id)",
        "CREATE INDEX ix_tag_new_targets ON tag_new_targets(tag_id)",
    )
    for statement in statements:
        cur.execute(statement)
