"""Utilities for working with the VocaDB data dump.

The dump is a flat archive of six folders, one per entry type:

- Artists/ Albums/ Songs/ EventSeries/ Events/ Tags/

- Each folder holds chunk files named ``{n}.json``

- Every file is a JSON array of up to 1000 entries
"""

import json
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import requests

from vdbpy.types.dump import (
    DumpAlbum,
    DumpArtist,
    DumpEvent,
    DumpEventSeries,
    DumpSong,
    DumpTag,
)
from vdbpy.utils.cache import get_vdbpy_cache_dir
from vdbpy.utils.logger import get_logger

DUMP_URL = "https://vocaloid.eu/vocadb/dump.zip"

logger = get_logger()


def get_dump_path() -> Path:
    """Return the path to dump.zip, downloading it if not present."""
    dump_path = get_vdbpy_cache_dir() / "dump.zip"
    if not dump_path.exists():
        logger.info(f"Downloading dump from {DUMP_URL}...")
        response = requests.get(DUMP_URL, stream=True, timeout=300)
        response.raise_for_status()
        with dump_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Dump saved to '{dump_path}'")
    return dump_path


@dataclass
class Dump:
    """Typed accessor, lazy yielding to keep the memory low."""

    path: Path

    @classmethod
    def load(cls, dump_path: Path | None = None) -> "Dump":
        return cls(dump_path or get_dump_path())

    def _iter(self, folder: str) -> Iterator[dict]:
        with zipfile.ZipFile(self.path) as z:
            for name in sorted(z.namelist()):
                if name.startswith(f"{folder}/") and name.endswith(".json"):
                    yield from json.loads(z.read(name))

    def artists(self) -> Iterator[DumpArtist]:
        return (DumpArtist.from_dict(e) for e in self._iter("Artists"))

    def albums(self) -> Iterator[DumpAlbum]:
        return (DumpAlbum.from_dict(e) for e in self._iter("Albums"))

    def songs(self) -> Iterator[DumpSong]:
        return (DumpSong.from_dict(e) for e in self._iter("Songs"))

    def event_series(self) -> Iterator[DumpEventSeries]:
        return (DumpEventSeries.from_dict(e) for e in self._iter("EventSeries"))

    def events(self) -> Iterator[DumpEvent]:
        return (DumpEvent.from_dict(e) for e in self._iter("Events"))

    def tags(self) -> Iterator[DumpTag]:
        return (DumpTag.from_dict(e) for e in self._iter("Tags"))


def _load_cache(cache_path: Path, dump_mtime: float) -> dict | None:
    if not cache_path.exists():
        return None
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    if data.get("dump_mtime") != dump_mtime:
        return None
    return data["map"]


def _save_cache(cache_path: Path, mapping: dict, dump_mtime: float) -> None:
    cache_path.write_text(
        json.dumps({"dump_mtime": dump_mtime, "map": mapping}),
        encoding="utf-8",
    )


def _resolve_parents(direct_parent: dict[int, int]) -> dict[int, int]:
    def resolve(item_id: int, seen: set[int]) -> int:
        if item_id in seen:
            return item_id  # cycle guard
        parent = direct_parent.get(item_id)
        if parent is None:
            return item_id
        seen.add(item_id)
        return resolve(parent, seen)

    all_ids = set(direct_parent.keys()) | set(direct_parent.values())
    return {item_id: resolve(item_id, set()) for item_id in all_ids}


def build_base_voicebank_map(dump_path: Path | None = None) -> dict[int, int]:
    """Return a mapping of every artist id to its ultimate base voicebank id.

    Artists with no base voicebank map to themselves. Result is cached to disk.
    """
    if dump_path is None:
        dump_path = get_dump_path()

    cache_path = dump_path.parent / "base_voicebank_map.json"
    dump_mtime = dump_path.stat().st_mtime
    raw = _load_cache(cache_path, dump_mtime)
    if raw is not None:
        logger.info("Loaded base voicebank map from cache.")
        return {int(k): v for k, v in raw.items()}

    logger.info("Building base voicebank map from dump...")
    direct_parent: dict[int, int] = {}
    for artist in Dump.load(dump_path).artists():
        if artist.base_voicebank:
            direct_parent[artist.id] = artist.base_voicebank.id

    result = _resolve_parents(direct_parent)
    _save_cache(cache_path, result, dump_mtime)
    return result


def build_tag_parent_map(dump_path: Path | None = None) -> dict[int, int]:
    """Return a mapping of every tag id to its ultimate root parent tag id.

    Tags with no parent map to themselves. Result is cached to disk.
    """
    if dump_path is None:
        dump_path = get_dump_path()

    cache_path = dump_path.parent / "tag_parent_map.json"
    dump_mtime = dump_path.stat().st_mtime
    raw = _load_cache(cache_path, dump_mtime)
    if raw is not None:
        logger.info("Loaded tag parent map from cache.")
        return {int(k): v for k, v in raw.items()}

    logger.info("Building tag parent map from dump...")
    direct_parent: dict[int, int] = {}
    for tag in Dump.load(dump_path).tags():
        if tag.parent:
            direct_parent[tag.id] = tag.parent.id

    result = _resolve_parents(direct_parent)
    _save_cache(cache_path, result, dump_mtime)
    return result


def build_tag_direct_parent_map(dump_path: Path | None = None) -> dict[int, int]:
    """Return a mapping of tag id to its direct parent tag id.

    Tags with no parent are not included. Result is cached to disk.
    """
    if dump_path is None:
        dump_path = get_dump_path()

    cache_path = dump_path.parent / "tag_direct_parent_map.json"
    dump_mtime = dump_path.stat().st_mtime
    raw = _load_cache(cache_path, dump_mtime)
    if raw is not None:
        logger.info("Loaded tag direct parent map from cache.")
        return {int(k): v for k, v in raw.items()}

    logger.info("Building tag direct parent map from dump...")
    result: dict[int, int] = {}
    for tag in Dump.load(dump_path).tags():
        if tag.parent:
            result[tag.id] = tag.parent.id

    _save_cache(cache_path, result, dump_mtime)
    return result


def build_tag_info_map(dump_path: Path | None = None) -> dict[int, tuple[str, str]]:
    """Return a mapping of tag id to (name, categoryName) from the dump.

    Result is cached to disk.
    """
    if dump_path is None:
        dump_path = get_dump_path()

    cache_path = dump_path.parent / "tag_info_map.json"
    dump_mtime = dump_path.stat().st_mtime
    raw = _load_cache(cache_path, dump_mtime)
    if raw is not None:
        logger.info("Loaded tag info map from cache.")
        return {int(k): (v[0], v[1]) for k, v in raw.items()}

    logger.info("Building tag info map from dump...")
    result: dict[int, tuple[str, str]] = {}
    for tag in Dump.load(dump_path).tags():
        name = tag.translated_name
        tag_name = ""
        if name:
            tag_name = name.english or name.romaji or name.japanese
        result[tag.id] = (tag_name, tag.category_name)

    _save_cache(cache_path, {k: list(v) for k, v in result.items()}, dump_mtime)
    return result
