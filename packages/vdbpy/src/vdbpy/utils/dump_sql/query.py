"""Query surface of the dump database: ``DumpDB`` and the read-only SQL sandbox."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import Row, create_engine, text

from vdbpy.utils.dump import get_dump_path
from vdbpy.utils.dump_sql.build import ingest, memory_note, stored_mtime
from vdbpy.utils.dump_sql.models import (
    Album,
    AlbumEvent,
    Artist,
    ArtistGroup,
    ArtistMember,
    Base,
    EntryName,
    EntryTag,
    Event,
    EventSeries,
    Song,
    SongArtist,
    SongEvent,
    SongPV,
    Tag,
)
from vdbpy.utils.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy import Engine
    from sqlalchemy.sql import Select

_Row = TypeVar("_Row", bound=tuple)
_T = TypeVar("_T")

logger = get_logger()

ENTRY_TABLES = ("songs", "albums", "artists", "events", "event_series", "tags")

_READONLY_ACTIONS = frozenset(
    {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }
)


class SqlError(Exception):
    """Raised when an ad-hoc SQL query is rejected or fails."""


@dataclass
class SqlResult:
    columns: list[str]
    rows: list[tuple]
    truncated: bool


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
            row[2] for row in conn.exec_driver_sql(f'PRAGMA index_info("{name}")').all()
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
        """Wrap an already-built SQLite dump database. Prefer `DumpDB.build()`."""
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
            if stored_mtime(engine) == dump_mtime:
                logger.info("Loaded preprocessed dump database from cache.")
                return cls(engine, db_path)
            logger.info(
                f"Discarding the stale dump database at '{db_path}'"
                " (it does not match the current dump)"
            )
            engine.dispose()
            db_path.unlink()

        logger.info(
            f"Building preprocessed dump database from '{dump_path}'"
            f" ({dump_path.stat().st_size / 1024 / 1024:.0f} MB){memory_note()}"
        )
        start = time.monotonic()
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        try:
            ingest(engine, dump_path, dump_mtime)
        except BaseException:
            engine.dispose()
            db_path.unlink(missing_ok=True)
            raise
        logger.info(
            f"Built dump database in {time.monotonic() - start:.1f}s:"
            f" {db_path.stat().st_size / 1024 / 1024:.0f} MB{memory_note()}"
        )
        return cls(engine, db_path)

    def exec(self, stmt: Select[_Row]) -> Sequence[Row[_Row]]:
        with self.engine.connect() as conn:
            return conn.execute(stmt).all()

    def scalars(self, stmt: Select[tuple[_T]]) -> list[_T]:
        with self.engine.connect() as conn:
            return list(conn.scalars(stmt).all())

    def schema_sql(self) -> str:
        with self.engine.connect() as conn:
            return _format_schema(conn)

    def max_entry_ids(self) -> dict[str, int]:
        with self.engine.connect() as conn:
            return {
                table: conn.execute(
                    text(f"SELECT COALESCE(MAX(id), 0) FROM {table}"),  # noqa: S608
                ).scalar_one()
                for table in ENTRY_TABLES
            }

    def count_ids_above(self, maxima: dict[str, int]) -> dict[str, int]:
        # Used to report how many entries are new compared to an older dump.
        with self.engine.connect() as conn:
            return {
                table: conn.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE id > :max_id"),  # noqa: S608
                    {"max_id": maxima[table]},
                ).scalar_one()
                for table in ENTRY_TABLES
                if table in maxima
            }

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
                lambda: int(time.monotonic() > deadline),
                10_000,
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
