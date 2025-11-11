from typing import Any

from vdbpy.parsers.albums import parse_song_albums
from vdbpy.parsers.artists import parse_artist_participation
from vdbpy.parsers.events import parse_release_event
from vdbpy.parsers.shared import (
    parse_base_entry,
    parse_base_entry_version,
    parse_event_ids,
    parse_links,
    parse_names,
    parse_pvs,
    parse_version_artist_participation,
)
from vdbpy.parsers.tags import parse_tag
from vdbpy.types.songs import (
    Lyrics,
    OptionalSongFieldNames,
    OptionalSongFields,
    SongEntry,
    SongVersion,
)
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger

logger = get_logger()


def parse_lyrics(lyrics: dict[Any, Any]) -> list[Lyrics]:
    return [
        Lyrics(
            language_codes=lyric.get("cultureCodes", []),
            lyrics_id=lyric["id"],
            source=lyric.get("source", ""),
            translation_type=lyric["translationType"],
            url=lyric.get("url", ""),
            value=lyric.get("value", ""),
        )
        for lyric in lyrics
    ]


def parse_languages(data: dict[Any, Any]) -> list[str]:
    # DUMB function for now
    # TODO improve
    lang_codes: list[str] = []
    for code in data:
        lang_codes.append(code)  # noqa: PERF402
    return lang_codes


def parse_optional_song_fields(
    data: dict[Any, Any], fields: set[OptionalSongFieldNames] | None = None
) -> OptionalSongFields:
    names = "Unknown"
    aliases = "Unknown"
    if "names" in data:
        names, aliases = parse_names(data["names"])
    return OptionalSongFields(
        lyrics=parse_lyrics(data["lyrics"])
        if ("lyrics" in data and fields and "lyrics" in fields)
        else "Unknown",
        albums=parse_song_albums(data["albums"])
        if ("albums" in data and fields and "albums" in fields)
        else "Unknown",
        artists=parse_artist_participation(data["artists"])
        if ("artists" in data and fields and "artists" in fields)
        else "Unknown",
        names=names,
        aliases=aliases,
        pvs=parse_pvs(data["pvs"])
        if ("pvs" in data and fields and "pvs" in fields)
        else "Unknown",
        release_events=[parse_release_event(event) for event in data["releaseEvents"]]
        if ("releaseEvents" in data and fields and "releaseEvent" in fields)
        else "Unknown",
        tags=[parse_tag(tag) for tag in data["tags"]]
        if ("tags" in data and fields and "tags" in fields)
        else "Unknown",
        external_links=parse_links(data)
        if ("webLinks" in data and fields and "webLinks" in fields)
        else "Unknown",
        max_milli_bpm=data.get("maxMilliBpm")
        if fields and "bpm" in fields
        else "Unknown",
        min_milli_bpm=data.get("minMilliBpm")
        if fields and "bpm" in fields
        else "Unknown",
        languages=parse_languages(data["cultureCodes"])
        if "cultureCodes" in data and fields and "cultureCodes" in fields
        else "Unknown",
    )


def parse_song(
    data: dict[Any, Any], fields: set[OptionalSongFieldNames] | None = None
) -> SongEntry:
    logger.debug(f"Parsing song: {data}")
    base_entry = parse_base_entry(data)
    optional_song_fields = parse_optional_song_fields(data, fields)
    return SongEntry(
        artist_string=data["artistString"],
        favorite_count=data["favoritedTimes"],
        length_seconds=data["lengthSeconds"],
        original_version_id=data.get("originalVersionId", 0),
        publish_date=parse_date(data["publishDate"]) if "publishDate" in data else None,
        pv_services=data["pvServices"].split(", "),
        rating_score=data["ratingScore"],
        song_type=data["songType"],
        **base_entry.__dict__,
        **optional_song_fields.__dict__,
    )


def verify_song_version_fields(data: dict[Any, Any]) -> None:
    data_keys = set(data.keys())
    assert data_keys == {  # noqa: S101
        "song",
        "archivedVersion",
        "comparableVersions",
        "name",
        "versions",
    }
    version_data = data["versions"]["firstData"]
    version_keys = sorted(version_data.keys())

    # Check that all fields are accounted for:
    known_version_fields = [
        "artists",
        "id",
        "lengthSeconds",
        "lyrics",
        "names",
        "notes",
        "pvs",
        "songType",
        "translatedName",
        "webLinks",
    ]

    potentially_missing_version_fields = [
        "notesEng",
        "publishDate",
        "originalVersion",
        "releaseEvents",
        "releaseEvent",
        "maxMilliBpm",
        "minMilliBpm",
    ]

    skipped_fields = ["albums", "nicoId"]

    for field in known_version_fields:
        try:
            version_keys.remove(field)
        except ValueError:
            msg = f"Unknown field '{field}' for {data}"
            raise ValueError(msg)  # noqa: B904

    for field in [*potentially_missing_version_fields, *skipped_fields]:
        try:
            version_keys.remove(field)
        except ValueError:
            logger.debug(f"Missing field {field}")

    if version_keys:
        msg = "Unknown fields: " + ", ".join(version_keys)
        raise ValueError(msg)


def parse_song_version(data: dict[Any, Any]) -> SongVersion:
    version_data = data["versions"]["firstData"]
    return SongVersion(
        artists=parse_version_artist_participation(version_data["artists"]),
        length_seconds=version_data.get("lengthSeconds", 0),
        lyrics=parse_lyrics(version_data["lyrics"]),
        max_milli_bpm=version_data.get("maxMilliBpm", 0),
        min_milli_bpm=version_data.get("minMilliBpm", 0),
        original_version_id=version_data["originalVersion"]["id"]
        if "originalVersion" in version_data
        else 0,
        publish_date=parse_date(version_data["publishDate"])
        if "publishDate" in version_data
        else None,
        pvs=parse_pvs(version_data["pvs"]),
        release_event_ids=parse_event_ids(version_data),
        song_type=version_data["songType"],
        **parse_base_entry_version(data).__dict__,
    )
