"""Dataclasses for the data dump entries."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from vdbpy.parsers.shared import parse_links, parse_names, parse_pvs
from vdbpy.types.shared import PV, DefaultLanguage, ExternalLink
from vdbpy.utils.date import parse_date

# -------- # shared # -------- #


@dataclass
class ObjectRef:
    id: int
    name_hint: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ObjectRef | None":
        if not data:
            return None
        return cls(id=data["id"], name_hint=data.get("nameHint", ""))


@dataclass
class TranslatedName:
    japanese: str
    romaji: str
    english: str
    default: str
    default_language: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TranslatedName | None":
        if not data:
            return None
        return cls(
            japanese=data.get("japanese", ""),
            romaji=data.get("romaji", ""),
            english=data.get("english", ""),
            default=data.get("default", ""),
            default_language=data.get("defaultLanguage", "Unspecified"),
        )


@dataclass
class TagUsage:
    count: int
    tag: ObjectRef | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TagUsage":
        return cls(count=data.get("count", 0), tag=ObjectRef.from_dict(data.get("tag")))


# -------- # helpers # -------- #


def _date(value: str | None) -> datetime | None:
    return parse_date(value) if value else None


def _names(data: dict[str, Any]) -> tuple[dict[DefaultLanguage, str], list[str]]:
    raw = data.get("names")
    return parse_names(raw) if raw else ({}, [])


def _pvs(data: dict[str, Any]) -> list[PV]:
    raw = data.get("pvs")
    return parse_pvs(raw) if raw else []


def _tags(data: dict[str, Any]) -> list[TagUsage]:
    return [TagUsage.from_dict(t) for t in data.get("tags") or []]


def _refs(data: dict[str, Any], key: str) -> list[ObjectRef]:
    refs = (ObjectRef.from_dict(r) for r in data.get(key) or [])
    return [r for r in refs if r is not None]


# -------- # entries # -------- #


@dataclass
class DumpArtist:
    id: int
    artist_type: str
    base_voicebank: ObjectRef | None
    release_date: datetime | None
    culture_codes: list[str]
    description: str
    description_eng: str
    translated_name: TranslatedName | None
    names: dict[DefaultLanguage, str]
    aliases: list[str]
    web_links: list[ExternalLink]
    groups: list[Any]
    members: list[Any]
    tags: list[TagUsage]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DumpArtist":
        names, aliases = _names(data)
        return cls(
            id=data["id"],
            artist_type=data.get("artistType", "Unknown"),
            base_voicebank=ObjectRef.from_dict(data.get("baseVoicebank")),
            release_date=_date(data.get("releaseDate")),
            culture_codes=list(data.get("cultureCodes") or []),
            description=data.get("description") or "",
            description_eng=data.get("descriptionEng") or "",
            translated_name=TranslatedName.from_dict(data.get("translatedName")),
            names=names,
            aliases=aliases,
            web_links=parse_links(data),
            groups=list(data.get("groups") or []),
            members=list(data.get("members") or []),
            tags=_tags(data),
        )


@dataclass
class DumpAlbum:
    id: int
    disc_type: str
    translated_name: TranslatedName | None
    names: dict[DefaultLanguage, str]
    aliases: list[str]
    description: str
    original_release: dict[str, Any] | None
    pvs: list[PV]
    web_links: list[ExternalLink]
    artists: list[Any]
    songs: list[Any]
    discs: list[Any]
    identifiers: list[Any]
    tags: list[TagUsage]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DumpAlbum":
        names, aliases = _names(data)
        return cls(
            id=data["id"],
            disc_type=data.get("discType", "Unknown"),
            translated_name=TranslatedName.from_dict(data.get("translatedName")),
            names=names,
            aliases=aliases,
            description=data.get("description") or "",
            original_release=data.get("originalRelease"),
            pvs=_pvs(data),
            web_links=parse_links(data),
            artists=list(data.get("artists") or []),
            songs=list(data.get("songs") or []),
            discs=list(data.get("discs") or []),
            identifiers=list(data.get("identifiers") or []),
            tags=_tags(data),
        )


@dataclass
class DumpSong:
    id: int
    song_type: str
    length_seconds: int
    nico_id: str
    publish_date: datetime | None
    min_milli_bpm: int | None
    max_milli_bpm: int | None
    translated_name: TranslatedName | None
    names: dict[DefaultLanguage, str]
    aliases: list[str]
    notes: str
    notes_eng: str
    culture_codes: list[str]
    original_version: ObjectRef | None
    release_events: list[ObjectRef]
    pvs: list[PV]
    web_links: list[ExternalLink]
    artists: list[Any]
    albums: list[Any]
    lyrics: list[Any]
    tags: list[TagUsage]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DumpSong":
        names, aliases = _names(data)
        return cls(
            id=data["id"],
            song_type=data.get("songType", "Unspecified"),
            length_seconds=data.get("lengthSeconds", 0),
            nico_id=data.get("nicoId") or "",
            publish_date=_date(data.get("publishDate")),
            min_milli_bpm=data.get("minMilliBpm"),
            max_milli_bpm=data.get("maxMilliBpm"),
            translated_name=TranslatedName.from_dict(data.get("translatedName")),
            names=names,
            aliases=aliases,
            notes=data.get("notes") or "",
            notes_eng=data.get("notesEng") or "",
            culture_codes=list(data.get("cultureCodes") or []),
            original_version=ObjectRef.from_dict(data.get("originalVersion")),
            release_events=_refs(data, "releaseEvents"),
            pvs=_pvs(data),
            web_links=parse_links(data),
            artists=list(data.get("artists") or []),
            albums=list(data.get("albums") or []),
            lyrics=list(data.get("lyrics") or []),
            tags=_tags(data),
        )


@dataclass
class DumpEventSeries:
    id: int
    category: str
    translated_name: TranslatedName | None
    names: dict[DefaultLanguage, str]
    aliases: list[str]
    description: str
    web_links: list[ExternalLink]
    tags: list[TagUsage]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DumpEventSeries":
        names, name_aliases = _names(data)
        aliases = list(data.get("aliases") or []) + name_aliases
        return cls(
            id=data["id"],
            category=data.get("category", "Unspecified"),
            translated_name=TranslatedName.from_dict(data.get("translatedName")),
            names=names,
            aliases=aliases,
            description=data.get("description") or "",
            web_links=parse_links(data),
            tags=_tags(data),
        )


@dataclass
class DumpEvent:
    id: int
    category: str
    date: datetime | None
    series: ObjectRef | None
    series_number: int
    venue: ObjectRef | None
    venue_name: str
    song_list: ObjectRef | None
    translated_name: TranslatedName | None
    names: dict[DefaultLanguage, str]
    aliases: list[str]
    description: str
    pvs: list[PV]
    web_links: list[ExternalLink]
    artists: list[Any]
    tags: list[TagUsage]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DumpEvent":
        names, aliases = _names(data)
        return cls(
            id=data["id"],
            category=data.get("category", "Unspecified"),
            date=_date(data.get("date")),
            series=ObjectRef.from_dict(data.get("series")),
            series_number=data.get("seriesNumber", 0),
            venue=ObjectRef.from_dict(data.get("venue")),
            venue_name=data.get("venueName") or "",
            song_list=ObjectRef.from_dict(data.get("songList")),
            translated_name=TranslatedName.from_dict(data.get("translatedName")),
            names=names,
            aliases=aliases,
            description=data.get("description") or "",
            pvs=_pvs(data),
            web_links=parse_links(data),
            artists=list(data.get("artists") or []),
            tags=_tags(data),
        )


@dataclass
class DumpTag:
    id: int
    category_name: str
    parent: ObjectRef | None
    related_tags: list[ObjectRef]
    targets: Any
    new_targets: list[str]
    hide_from_suggestions: bool
    translated_name: TranslatedName | None
    names: dict[DefaultLanguage, str]
    aliases: list[str]
    description: str
    description_eng: str
    web_links: list[ExternalLink] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DumpTag":
        names, aliases = _names(data)
        return cls(
            id=data["id"],
            category_name=data.get("categoryName") or "",
            parent=ObjectRef.from_dict(data.get("parent")),
            related_tags=_refs(data, "relatedTags"),
            targets=data.get("targets"),
            new_targets=list(data.get("newTargets") or []),
            hide_from_suggestions=data.get("hideFromSuggestions", False),
            translated_name=TranslatedName.from_dict(data.get("translatedName")),
            names=names,
            aliases=aliases,
            description=data.get("description") or "",
            description_eng=data.get("descriptionEng") or "",
            web_links=parse_links(data),
        )
