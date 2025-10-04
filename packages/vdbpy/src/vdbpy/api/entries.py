import random
from datetime import UTC, datetime
from typing import get_args

from vdbpy.config import WEBSITE
from vdbpy.types import (
    PV,
    AlbumParticipation,
    AlbumTrack,
    AlbumVersion,
    ArtistParticipation,
    ArtistVersion,
    Disc,
    Edit_type,
    Entry_type,
    EventArtistParticipation,
    EventParticipation,
    EventSeriesRelation,
    ExternalLink,
    Lyrics,
    Picture,
    ReleaseEventSeriesVersion,
    ReleaseEventVersion,
    SonglistRelation,
    SongVersion,
    TagRelation,
    TagVersion,
    UserEdit,
    VenueRelation,
    VenueVersion,
)
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount, fetch_json

logger = get_logger()

edit_event_map: dict[str, Edit_type] = {
    "PropertiesUpdated": "Updated",
    "Updated": "Updated",
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


# --------------- Shared version parsers --------------- #


def parse_names(data: dict) -> tuple[str, str, str, list[str]]:
    name_non_english = ""
    name_romaji = ""
    name_english = ""
    aliases: list[str] = []

    for entry in data["names"]:
        language = entry["language"]
        value = entry["value"]
        match language:
            case "Japanese":
                name_non_english = value
            case "Romaji":
                name_romaji = value
            case "English":
                name_english = value
            case "Unspecified":
                aliases.append(value)

    return name_non_english, name_romaji, name_english, aliases


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


def parse_event_participations(data) -> list[EventParticipation]:
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
    raw_links = []
    if "externalLinks" in data:
        raw_links = data["externalLinks"]
    elif "webLinks" in data:  # inconsistent naming
        raw_links = data["webLinks"]

    if not raw_links:
        return []

    links = []
    for link in raw_links:
        links.append(
            ExternalLink(
                category=link["category"],
                description=link["description"],
                disabled=link["disabled"],
                url=link["url"],
            )
        )
    return links


def parse_pictures(data) -> list[Picture]:
    if "pictures" not in data or not data["pictures"]:
        return []
    pictures = []
    for picture in data["pictures"]:
        pictures.append(
            Picture(
                picture_id=picture["id"],
                mime=picture["mime"],
                name=picture["name"],
            )
        )
    return pictures


# --------------- Version parsers --------------- #


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

    def parse_lyrics(data) -> list[Lyrics]:
        if "lyrics" not in data or not data["lyrics"]:
            return []
        lyrics = []
        for lyric in data["lyrics"]:
            lyrics.append(
                Lyrics(
                    language_codes=lyric.get("cultureCodes", []),
                    lyrics_id=lyric["id"],
                    source=lyric.get("source", ""),
                    translation_type=lyric["translationType"],
                    url=lyric.get("url", ""),
                    value=lyric.get("value", ""),
                )
            )
        return lyrics

    name_non_english, name_romaji, name_english, aliases = parse_names(data)
    raw_dnm = data["translatedName"]["defaultLanguage"]
    default_name_language = "Non-English" if raw_dnm == "Japanese" else raw_dnm

    return SongVersion(
        albums=parse_album_participation(data),
        aliases=aliases,
        artist=parse_artist_participation(data),
        default_name_language=default_name_language,
        description_eng=data.get("notesEng", ""),
        description=data.get("notes", ""),
        external_links=parse_links(data),
        entry_id=data["id"],
        length=data["lengthSeconds"],
        lyrics=parse_lyrics(data),
        name_non_english=name_non_english,
        name_romaji=name_romaji,
        name_english=name_english,
        original_version_id=data["originalVersion"]["id"]
        if "originalVersion" in data
        else 0,
        publish_date=parse_date(data["publishDate"]) if "publishDate" in data else None,
        pvs=parse_pvs(data),
        release_events=parse_event_participations(data),
        song_type=data["songType"],
        status=entry_status,
    )


def parse_album_version(data: dict) -> AlbumVersion:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]

    def parse_discs(data) -> list[Disc]:
        if "discs" not in data or not data["discs"]:
            return []
        discs = []
        for disc in data["discs"]:
            discs.append(
                Disc(
                    disc_number=disc["discNumber"],
                    disc_id=disc["id"],
                    media_type=disc["mediaType"],
                    name=disc["name"],
                )
            )
        return discs

    def parse_album_tracks(data) -> list[AlbumTrack]:
        if "songs" not in data or not data["songs"]:
            return []
        album_tracks = []
        for album_track in data["songs"]:
            album_tracks.append(
                AlbumTrack(
                    disc_number=album_track["discNumber"],
                    track_number=album_track["trackNumber"],
                    song_id=album_track["id"],
                    name_hint=album_track["nameHint"],
                )
            )
        return album_tracks

    def parse_album_publish_date(data) -> tuple[datetime | None, int, int, int]:
        year = data.get("year", 0)
        month = data.get("month", 0)
        day = data.get("day", 0)
        publish_date = (
            datetime(year, month, day, tzinfo=UTC) if year and month and day else None
        )
        return publish_date, year, month, day

    publish_date, year, month, day = parse_album_publish_date(
        data["originalRelease"]["releaseDate"]
    )

    name_non_english, name_romaji, name_english, aliases = parse_names(data)
    raw_dnm = data["translatedName"]["defaultLanguage"]
    default_name_language = "Non-English" if raw_dnm == "Japanese" else raw_dnm

    return AlbumVersion(
        album_type=data["discType"],
        aliases=aliases,
        artists=parse_artist_participation(data),
        barcodes=[code["value"] for code in data["identifiers"]]
        if "identifiers" in data
        else [],
        catalog_number=data["originalRelease"].get("catNum", ""),
        default_name_language=default_name_language,
        description_eng=data.get("descriptionEng", ""),
        description=data.get("description", ""),
        discs=parse_discs(data),
        external_links=parse_links(data),
        entry_id=data["id"],
        name_non_english=name_non_english,
        name_romaji=name_romaji,
        name_english=name_english,
        additional_pictures=parse_pictures(data),
        publish_date=publish_date,
        publish_day=day,
        publish_month=month,
        publish_year=year,
        pvs=parse_pvs(data),  # 'publish_date': None, 'length': 0,
        release_events=parse_event_participations(data["originalRelease"]),
        songs=parse_album_tracks(data),
        status=entry_status,
    )


def parse_artist_version(data: dict) -> ArtistVersion:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]
    name_non_english, name_romaji, name_english, aliases = parse_names(data)
    raw_dnm = data["translatedName"]["defaultLanguage"]
    default_name_language = "Non-English" if raw_dnm == "Japanese" else raw_dnm

    def parse_groups(data) -> dict[str, list[int]]:
        group_link_types = [
            "CharacterDesigner",
            "Group",
            "Illustrator",
            "Manager",
            "VoiceProvider",
        ]
        groups_by_link_type = {
            group_link_type: [] for group_link_type in group_link_types
        }
        for group in data["groups"]:
            link_type = group["linkType"]
            if link_type not in group_link_types:
                logger.warning(f"Unknown link type '{link_type} for Ar/{data['id']}")
            groups_by_link_type[link_type].append(group["id"])
        return groups_by_link_type

    groups_by_link_type = parse_groups(data)
    return ArtistVersion(
        additional_pictures=parse_pictures(data),
        aliases=aliases,
        artist_type=data["artistType"],
        default_name_language=default_name_language,
        description_eng=data["descriptionEng"],
        description=data["description"],
        entry_id=data["id"],
        external_links=parse_links(data),
        group_ids=groups_by_link_type["Group"],
        name_english=name_english,
        name_non_english=name_non_english,
        name_romaji=name_romaji,
        status=entry_status,
        vb_base_id=data["baseVoicebank"]["id"] if "baseVoicebank" in data else 0,
        vb_chara_designer_ids=groups_by_link_type["CharacterDesigner"],
        vb_illustrator_ids=groups_by_link_type["Illustrator"],
        vb_manager_ids=groups_by_link_type["Manager"],
        vb_voice_provider_ids=groups_by_link_type["VoiceProvider"],
        vb_release_date=parse_date(data["releaseDate"])
        if "releaseDate" in data
        else None,
    )


def parse_tag_version(data: dict) -> TagVersion:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]
    name_non_english, name_romaji, name_english, aliases = parse_names(data)
    raw_dnm = data["translatedName"]["defaultLanguage"]
    default_name_language = "Non-English" if raw_dnm == "Japanese" else raw_dnm

    def parse_tag_relation(data) -> TagRelation:
        return TagRelation(
            tag_id=data["id"],
            name_hint=data["nameHint"],
        )

    return TagVersion(
        aliases=aliases,
        default_name_language=default_name_language,
        description_eng=data["descriptionEng"],
        description=data["description"],
        entry_id=data["id"],
        external_links=parse_links(data),
        name_english=name_english,
        name_non_english=name_non_english,
        name_romaji=name_romaji,
        status=entry_status,
        tag_category=data["categoryName"],
        hidden_from_suggestions=data["hideFromSuggestions"],
        parent_tag=parse_tag_relation(data["parent"]) if "parent" in data else None,
        related_tags=[parse_tag_relation(tag) for tag in data["relatedTags"]],
    )


def parse_release_event_version(data: dict) -> ReleaseEventVersion:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]
    autofilled_names = None
    if "names" in data:
        name_non_english, name_romaji, name_english, aliases = parse_names(data)
    else:
        name_non_english = name_romaji = name_english = ""
        aliases = []
        autofilled_names = data["translatedName"].values()
    raw_dnm = data["translatedName"]["defaultLanguage"]
    default_name_language = "Non-English" if raw_dnm == "Japanese" else raw_dnm

    def parse_event_series_relation(data) -> EventSeriesRelation:
        return EventSeriesRelation(
            series_id=data["id"],
            name_hint=data["nameHint"],
        )

    def parse_songlist_relation(data) -> SonglistRelation:
        return SonglistRelation(
            songlist_id=data["id"],
            name_hint=data["nameHint"],
        )

    def parse_venue_relation(data) -> VenueRelation:
        return VenueRelation(
            venue_id=data["id"],
            name_hint=data["nameHint"],
        )

    def parse_event_artists(data) -> list[EventArtistParticipation]:
        if "artists" not in data or not data["artists"]:
            return []
        event_artists = []
        for event_artist in data["artists"]:
            event_artists.append(
                EventArtistParticipation(
                    artist_id=event_artist["id"],
                    name_hint=event_artist["nameHint"],
                    roles=event_artist["roles"].split(", "),
                )
            )
        return event_artists

    return ReleaseEventVersion(
        aliases=aliases,
        artists=parse_event_artists(data),
        autofilled_names=autofilled_names,
        custom_venue_name=data.get("venueName", ""),
        default_name_language=default_name_language,
        description_eng=data.get("descriptionEng", ""),
        description=data.get("description", ""),
        entry_id=data["id"],
        event_category=data["category"],
        external_links=parse_links(data),
        name_english=name_english,
        name_non_english=name_non_english,
        name_romaji=name_romaji,
        series_number=data["seriesNumber"],
        series=parse_event_series_relation(data["series"])
        if "series" in data
        else None,
        songlist=parse_songlist_relation(data["songList"])
        if "songlist" in data
        else None,
        start_date=parse_date(data["date"]) if "date" in data else None,
        status=entry_status,
        venue=parse_venue_relation(data["venue"]) if "venue" in data else None,
    )


def parse_release_event_series_version(data: dict) -> ReleaseEventSeriesVersion:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]
    autofilled_names = None
    if "names" in data:
        name_non_english, name_romaji, name_english, aliases = parse_names(data)
    else:
        name_non_english = name_romaji = name_english = ""
        aliases = []
        autofilled_names = data["translatedName"].values()
    raw_dnm = data["translatedName"]["defaultLanguage"]
    default_name_language = "Non-English" if raw_dnm == "Japanese" else raw_dnm

    return ReleaseEventSeriesVersion(
        autofilled_names=autofilled_names,
        event_category=data["category"],
        aliases=aliases,
        default_name_language=default_name_language,
        description_eng=data.get("descriptionEng", ""),
        description=data.get("description", ""),
        entry_id=data["id"],
        external_links=parse_links(data),
        name_english=name_english,
        name_non_english=name_non_english,
        name_romaji=name_romaji,
        status=entry_status,
    )


def parse_venue_version(data: dict) -> VenueVersion:
    raise NotImplementedError


# --------------- --------------- #


def get_entry_versions(
    entry_type: Entry_type, entry_id: int, include_deleted=False
) -> list[UserEdit]:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/versions"
    data = fetch_json(url)
    if "deleted" in data["entry"] and data["entry"]["deleted"]:
        logger.warning(f"{entry_type} {entry_id} has been deleted.")
        if not include_deleted:
            return []
    return parse_edits_from_archived_versions(
        data["archivedVersions"], entry_type, entry_id
    )


@cache_without_expiration()
def get_raw_entry_version(entry_type: Entry_type, version_id: int) -> dict:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/versions/{version_id}"
    return fetch_json(url)


def get_entry_version(  # noqa: PLR0911
    entry_type: Entry_type, version_id: int
) -> (
    AlbumVersion
    | ArtistVersion
    | SongVersion
    | TagVersion
    | ReleaseEventVersion
    | ReleaseEventSeriesVersion
    | VenueVersion
):
    data = get_raw_entry_version(entry_type, version_id)
    match entry_type:
        case "Album":
            return parse_album_version(data)
        case "Artist":
            return parse_artist_version(data)
        case "Song":
            return parse_song_version(data)
        case "Tag":
            return parse_tag_version(data)
        case "ReleaseEvent":
            return parse_release_event_version(data)
        case "ReleaseEventSeries":
            return parse_release_event_series_version(data)
        case "Venue":
            return parse_venue_version(data)
        case _:
            raise Exception(f"Unknown entry type {entry_type}")
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
