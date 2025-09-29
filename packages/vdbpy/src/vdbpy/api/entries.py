import random
from typing import get_args

from vdbpy.config import WEBSITE
from vdbpy.types import (
    PV,
    AlbumParticipation,
    ArtistParticipation,
    Default_languages,
    Edit_type,
    Entry_type,
    EntryNames,
    EventParticipation,
    ExternalLink,
    Lyrics,
    SongVersion,
    UserEdit,
)
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount, fetch_json

logger = get_logger()

edit_event_map: dict[str, Edit_type] = {
    "PropertiesUpdated": "Updated",
    "Merged": "Updated",
    "Deleted": "Deleted",
    "Created": "Created",
}


def parse_edits_from_archived_versions(
    data: list[dict], entry_type: Entry_type, entry_id: int
) -> list[UserEdit]:
    parsed_edits: list[UserEdit] = []
    for edit_object in data:
        edit_type = edit_object["reason"]
        if edit_type == "Merged":
            logger.warning(
                f"Merge detected while parsing data for {entry_type} {entry_id} v{edit_object['id']}"
            )
            edit_type = "Updated"
        elif edit_type not in edit_event_map:
            logger.warning(
                f"Unknown edit type '{edit_type}' for {entry_type} {entry_id} v{edit_object['id']}"
            )
            edit_type = "Updated"
        else:
            edit_type = edit_event_map[edit_type]
        parsed_edits.append(
            UserEdit(
                user_id=edit_object["author"]["id"],
                edit_date=parse_date(edit_object["created"]),
                entry_type=entry_type,
                entry_id=entry_id,
                version_id=edit_object["id"],
                edit_event=edit_type,
                changed_fields=edit_object["changedFields"],
                update_notes=edit_object["notes"],
            )
        )
    return parsed_edits


def parse_song_version(data: dict) -> SongVersion:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]

    def parse_album_participation(data) -> list[AlbumParticipation]:
        if "albums" not in data or not data["albums"]:
            return []
        album_participations = []
        for album_participation in data["albums"]:
            album_participations.append(
                AlbumParticipation(
                    disc_number=album_participation["discNumber"],
                    track_number=album_participation["trackNumber"],
                    album_id=album_participation["id"],
                    name_hint=album_participation["nameHint"],
                )
            )
        return album_participations

    def parse_artist_participation(data) -> list[ArtistParticipation]:
        if "artists" not in data or not data["artists"]:
            return []
        artist_participations = []
        for artist_participation in data["artists"]:
            artist_participations.append(
                ArtistParticipation(
                    is_supporting=artist_participation["isSupport"],
                    artist_id=artist_participation["id"],
                    roles=artist_participation["roles"].split(", "),
                    name_hint=artist_participation["nameHint"],
                )
            )
        return artist_participations

    def parse_lyrics(data) -> list[Lyrics]:
        if "lyrics" not in data or not data["lyrics"]:
            return []
        lyrics = []
        for lyric in data["lyrics"]:
            lyrics.append(
                Lyrics(
                    language_codes=lyric.get("cultureCodes", []),
                    id=lyric["id"],
                    source=lyric.get("source", ""),
                    translation_type=lyric["translationType"],
                    url=lyric.get("url", ""),
                    value=lyric.get("value", ""),
                )
            )
        return lyrics

    def parse_pvs(data) -> list[PV]:
        if "pvs" not in data or not data["pvs"]:
            return []
        pvs: list[PV] = []
        for pv in data["pvs"]:
            pvs.append(
                PV(
                    author=pv["author"],
                    disabled=pv["disabled"],
                    length=pv["length"],
                    name=pv["name"],
                    pv_id=pv["pvId"],
                    pv_service=pv["service"],
                    pv_type=pv["pvType"],
                    publish_date=parse_date(pv["publishDate"])
                    if "publishDate" in pv
                    else None,
                )
            )
        return pvs

    def parse_events(data) -> list[EventParticipation]:
        if "releaseEvents" not in data or not data["releaseEvents"]:
            return []
        event_participations = []
        for event_participation in data["releaseEvents"]:
            event_participations.append(
                EventParticipation(
                    event_id=event_participation["id"],
                    name_hint=event_participation["nameHint"],
                )
            )
        return event_participations

    def parse_links(data) -> list[ExternalLink]:
        if "externalLinks" not in data or not data["externalLinks"]:
            return []
        links = []
        for link in data["externalLinks"]:
            links.append(
                ExternalLink(
                    category=link["category"],
                    id=link["id"],
                    url=link["url"],
                    description=link["description"],
                    description_url=link["descriptionUrl"],
                    disabled=link["disabled"],
                )
            )
        return links

    def parse_names(names: dict) -> tuple[list[EntryNames], list[str]]:
        primary_names: list[EntryNames] = []
        aliases: list[str] = []

        for language, value in names:
            if language in Default_languages:
                primary_names.append(EntryNames(language=language, value=value))
            else:
                aliases.append(value)

        return primary_names, aliases

    names, aliases = parse_names(data["names"])

    return SongVersion(
        status=entry_status,
        albums=parse_album_participation(data),
        artist=parse_artist_participation(data),
        length=data["lengthSeconds"],
        lyrics=parse_lyrics(data),
        original_version_id=data.get("originalVersionId", 0),
        publish_date=parse_date(data["publishDate"]) if "publishDate" in data else None,
        pvs=parse_pvs(data),
        release_events=parse_events(data),
        song_type=data["songType"],
        id=data["id"],
        default_name_language=data["translatedName"]["defaultLanguage"],
        names=names,
        aliases=aliases,
        description=data.get("description", ""),
        description_eng=data.get("descriptionEng", ""),
        external_links=parse_links(data),
        deleted=data.get("deleted", False),
    )


def get_entry_versions(entry_type: Entry_type, entry_id: int) -> list[UserEdit]:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/versions"
    data = fetch_json(url)
    if "deleted" in data["entry"] and data["entry"]["deleted"]:
        logger.warning(f"{entry_type} {entry_id} has been deleted.")
        return []
    return parse_edits_from_archived_versions(
        data["archivedVersions"], entry_type, entry_id
    )


@cache_without_expiration()
def get_raw_entry_version(entry_type: Entry_type, version_id: int) -> dict:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/versions/{version_id}"
    return fetch_json(url)


def get_entry_version(entry_type: Entry_type, version_id: int) -> dict | SongVersion:
    data = get_raw_entry_version(entry_type, version_id)
    if entry_type == "Song":
        return parse_song_version(data)
    # TODO proper return types
    return data["versions"]["firstData"]


@cache_with_expiration(days=1)
def get_cached_entry_count_by_entry_type(entry_type: str):
    url = f"{WEBSITE}/api/{add_s(entry_type)}?getTotalCount=True&maxResults=1"
    return fetch_cached_totalcount(url)


def get_random_entry():
    entry_type = random.choice(get_args(Entry_type))
    logger.info(f"Chose entry type '{entry_type}'")
    entry_type = add_s(entry_type)
    total = get_cached_entry_count_by_entry_type(entry_type)
    random_index = random.randint(1, total)
    url = f"{WEBSITE}/api/{entry_type}"
    params = {"getTotalCount": True, "maxResults": 1, "start": random_index}
    return fetch_json(url, params=params)["items"][0]


def is_deleted(entry_type: Entry_type, entry_id: int) -> bool:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}"
    entry = fetch_json(url)
    if "deleted" in entry:
        return entry["deleted"]
    return False


def delete_entry(
    session,
    entry_type: Entry_type,
    entry_id: int,
    force=False,
    deletion_msg="",
    prompt=True,
) -> bool:
    if is_deleted(entry_type, entry_id):
        logger.warning(f"Entry {entry_id} has already been deleted.")
        return False

    assert entry_type in get_args(Entry_type), "Invalid entry type"  # noqa: S101
    logger.warning(f"Deleting {entry_type} entry {entry_id}...")
    if prompt:
        _ = input("Press enter to delete...")

    if not force:
        # TODO comply with content removal guidelines
        logger.warning("Careful entry deletion has not been implemented.")
        return False
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}"
    if deletion_msg:
        url += f"?notes={deletion_msg}"

    deletion_attempt = session.delete(url)
    deletion_attempt.raise_for_status()

    return True
