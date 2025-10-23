import random
from datetime import UTC, datetime
from typing import (
    Callable,
    get_args,
)

from vdbpy.api.albums import get_albums_with_total_count
from vdbpy.api.artists import get_artists_with_total_count
from vdbpy.api.events import get_events_with_total_count
from vdbpy.api.series import get_many_series_with_total_count
from vdbpy.api.songlists import get_featured_songlists_with_total_count
from vdbpy.api.songs import get_songs_with_total_count
from vdbpy.api.tags import get_tags_with_total_count
from vdbpy.api.users import get_username_by_id, get_users_with_total_count
from vdbpy.api.venues import get_venues_with_total_count
from vdbpy.config import WEBSITE
from vdbpy.types.core import EditType, Entry, EntryType, UserEdit
from vdbpy.types.entry_versions import (
    PV,
    AlbumParticipation,
    AlbumTrack,
    AlbumVersion,
    ArtistParticipation,
    ArtistVersion,
    BaseEntryVersion,
    Disc,
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
    VenueRelation,
    VenueVersion,
)
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_cached_totalcount, fetch_json

logger = get_logger()

edit_event_map: dict[str, EditType] = {
    "PropertiesUpdated": "Updated",
    "Updated": "Updated",
    "Merged": "Updated",
    "Deleted": "Deleted",
    "Created": "Created",
}

entry_type_to_url: dict[EntryType, str] = {
    "Song": "S",
    "Artist": "Ar",
    "Album": "Al",
    "Venue": "Venue/Details",
    "Tag": "T",
    "ReleaseEvent": "E",
    "ReleaseEventSeries": "Es",
    "SongList": "L",
}

entry_url_to_type: dict[str, EntryType] = {v: k for k, v in entry_type_to_url.items()}


def parse_edits_from_archived_versions(
    data: list[dict], entry_type: EntryType, entry_id: int
) -> list[UserEdit]:
    parsed_edits: list[UserEdit] = []
    for edit_object in data:
        edit_type = edit_object["reason"]
        if edit_type == "Merged":
            logger.debug(
                f"Merge detected while parsing data for {entry_type} {entry_id} v{edit_object['id']}"
            )
            edit_type = "Updated"
        elif edit_type not in edit_event_map:
            logger.debug(
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

    if "names" in data:
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
    if "originalRelease" not in data:
        return []
    data = data["originalRelease"]
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


def parse_base_entry_version(data: dict) -> tuple[dict, BaseEntryVersion]:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]

    name_non_english, name_romaji, name_english, aliases = parse_names(data)
    raw_dnm = (
        data["translatedName"]["defaultLanguage"]
        if "translatedName" in data
        else "Unspecified"
    )
    default_name_language = "Non-English" if raw_dnm == "Japanese" else raw_dnm
    desc = data.get("notes", "") if "notes" in data else data.get("description", "")
    desc_eng = (
        data.get("notesEng", "") if "notes" in data else data.get("descriptionEng", "")
    )

    return data, BaseEntryVersion(
        aliases=aliases,
        default_name_language=default_name_language,
        description=desc,
        description_eng=desc_eng,
        entry_id=data["id"],
        external_links=parse_links(data),
        name_english=name_english,
        name_non_english=name_non_english,
        name_romaji=name_romaji,
        status=entry_status,
    )


def parse_song_version(data: dict) -> SongVersion:
    data, base_entry_version = parse_base_entry_version(data)

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

    return SongVersion(
        albums=parse_album_participation(data),
        artists=parse_artist_participation(data),
        length=data.get("lengthSeconds", 0),
        lyrics=parse_lyrics(data),
        original_version_id=data["originalVersion"]["id"]
        if "originalVersion" in data
        else 0,
        publish_date=parse_date(data["publishDate"]) if "publishDate" in data else None,
        pvs=parse_pvs(data),
        release_events=parse_event_participations(data),
        song_type=data["songType"],
        **base_entry_version.__dict__,
    )


def parse_album_version(data: dict) -> AlbumVersion:
    data, base_entry_version = parse_base_entry_version(data)

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
        if (
            "originalRelease" not in data
            or "releaseDate" not in data["originalRelease"]
        ):
            return None, 0, 0, 0

        data = data["originalRelease"]["releaseDate"]
        year = data.get("year", 0)
        month = data.get("month", 0)
        day = data.get("day", 0)
        publish_date = (
            datetime(year, month, day, tzinfo=UTC) if year and month and day else None
        )
        return publish_date, year, month, day

    publish_date, year, month, day = parse_album_publish_date(data)

    return AlbumVersion(
        album_type=data["discType"],
        artists=parse_artist_participation(data),
        barcodes=[code["value"] for code in data["identifiers"]]
        if "identifiers" in data
        else [],
        catalog_number=data["originalRelease"].get("catNum", "")
        if "originalRelease" in data
        else "",
        discs=parse_discs(data),
        additional_pictures=parse_pictures(data),
        publish_date=publish_date,
        publish_day=day,
        publish_month=month,
        publish_year=year,
        pvs=parse_pvs(data),  # 'publish_date': None, 'length': 0,
        release_events=parse_event_participations(data),
        songs=parse_album_tracks(data),
        **base_entry_version.__dict__,
    )


def parse_artist_version(data: dict) -> ArtistVersion:
    data, base_entry_version = parse_base_entry_version(data)

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
        artist_type=data["artistType"],
        group_ids=groups_by_link_type["Group"],
        vb_base_id=data["baseVoicebank"]["id"] if "baseVoicebank" in data else 0,
        vb_chara_designer_ids=groups_by_link_type["CharacterDesigner"],
        vb_illustrator_ids=groups_by_link_type["Illustrator"],
        vb_manager_ids=groups_by_link_type["Manager"],
        vb_voice_provider_ids=groups_by_link_type["VoiceProvider"],
        vb_release_date=parse_date(data["releaseDate"])
        if "releaseDate" in data
        else None,
        **base_entry_version.__dict__,
    )


def parse_tag_version(data: dict) -> TagVersion:
    data, base_entry_version = parse_base_entry_version(data)

    def parse_tag_relation(data) -> TagRelation:
        return TagRelation(
            tag_id=data["id"],
            name_hint=data["nameHint"],
        )

    return TagVersion(
        tag_category=data.get("categoryName", ""),
        hidden_from_suggestions=data.get("hideFromSuggestions", False),
        parent_tag=parse_tag_relation(data["parent"]) if "parent" in data else None,
        related_tags=[parse_tag_relation(tag) for tag in data["relatedTags"]]
        if "relatedTags" in data
        else [],
        **base_entry_version.__dict__,
    )


def parse_release_event_version(data: dict) -> ReleaseEventVersion:
    data, base_entry_version = parse_base_entry_version(data)
    autofilled_names = (
        data["translatedName"].values()
        if "names" not in data and "translatedName" in data
        else None
    )

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
        autofilled_names=autofilled_names,
        artists=parse_event_artists(data),
        custom_venue_name=data.get("venueName", ""),
        event_category=data["category"],
        series_number=data["seriesNumber"],
        series=parse_event_series_relation(data["series"])
        if "series" in data
        else None,
        songlist=parse_songlist_relation(data["songList"])
        if "songlist" in data
        else None,
        start_date=parse_date(data["date"]) if "date" in data else None,
        venue=parse_venue_relation(data["venue"]) if "venue" in data else None,
        **base_entry_version.__dict__,
    )


def parse_release_event_series_version(data: dict) -> ReleaseEventSeriesVersion:
    data, base_entry_version = parse_base_entry_version(data)
    autofilled_names = (
        data["translatedName"].values()
        if "names" not in data and "translatedName" in data
        else None
    )

    return ReleaseEventSeriesVersion(
        autofilled_names=autofilled_names,
        event_category=data["category"],
        **base_entry_version.__dict__,
    )


def parse_venue_version(data: dict) -> VenueVersion:
    data, base_entry_version = parse_base_entry_version(data)
    autofilled_names = (
        data["translatedName"].values()
        if "names" not in data and "translatedName" in data
        else None
    )

    coordinates = data.get("coordinates", {})
    return VenueVersion(
        autofilled_names=autofilled_names,
        address=data.get("address", None),
        country_code=data.get("addressCountryCode", None),
        latitude=coordinates.get("latitude", None),
        longitude=coordinates.get("longitude", None),
        **base_entry_version.__dict__,
    )


# --------------- --------------- #


def get_entry_details(entry_type: EntryType, entry_id: int) -> dict:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/details"
    return fetch_json(url)


@cache_with_expiration(days=1)
def is_entry_deleted(entry_type: EntryType, entry_id: int) -> bool:
    entry_details = get_entry_details(entry_type, entry_id)
    if "deleted" in entry_details:
        return entry_details["deleted"]
    return False


def get_edits_by_entry(
    entry_type: EntryType, entry_id: int, include_deleted=False
) -> list[UserEdit]:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}/versions"
    data = fetch_json(url)
    if not include_deleted:
        # print("Album", get_entry_versions("Album", 49682))
        # print("Tag", get_entry_versions("Tag", 9363))
        # print("ReleaseEvent", get_entry_versions("ReleaseEvent", 9785))
        # print("ReleaseEventSeries", get_entry_versions("ReleaseEventSeries", 997))
        if entry_type in ["Album", "Tag", "ReleaseEvent", "ReleaseEventSeries"]:
            if is_entry_deleted(entry_type, entry_id):
                logger.debug(f"{entry_type} {entry_id} has been deleted.")
                return []

        # print("Artist", get_entry_versions("Artist", 81663)) # works
        # print("Song", get_entry_versions("Song", 1)) # works
        # print("Venue", get_entry_versions("Venue", 418)) # works
        elif "deleted" in data["entry"] and data["entry"]["deleted"]:
            logger.debug(f"{entry_type} {entry_id} has been deleted.")
            return []

    return parse_edits_from_archived_versions(
        data["archivedVersions"], entry_type, entry_id
    )


@cache_without_expiration()
def get_edits_by_entry_before_version_id(
    entry_type: EntryType, entry_id: int, version_id: int, include_deleted=False
) -> list[UserEdit]:
    edits = get_edits_by_entry(entry_type, entry_id, include_deleted)
    return [edit for edit in edits if edit.version_id <= version_id]


@cache_without_expiration()
def get_raw_edit_by_entry(entry_type: EntryType, version_id: int) -> dict:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/versions/{version_id}"
    return fetch_json(url)


def get_entry_version(  # noqa: PLR0911
    entry_type: EntryType, version_id: int
) -> (
    AlbumVersion
    | ArtistVersion
    | SongVersion
    | TagVersion
    | ReleaseEventVersion
    | ReleaseEventSeriesVersion
    | VenueVersion
):
    data = get_raw_edit_by_entry(entry_type, version_id)
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
    entry_type = random.choice(get_args(EntryType))
    logger.info(f"Chose entry type '{entry_type}'")
    entry_type = add_s(entry_type)
    total = get_cached_entry_count_by_entry_type(entry_type)
    random_index = random.randint(1, total)
    url = f"{WEBSITE}/api/{entry_type}"
    params = {"getTotalCount": True, "maxResults": 1, "start": random_index}
    return fetch_json(url, params=params)["items"][0]


def is_deleted(entry_type: EntryType, entry_id: int) -> bool:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/{entry_id}"
    entry = fetch_json(url)
    if "deleted" in entry:
        return entry["deleted"]
    return False


def delete_entry(
    session,
    entry_type: EntryType,
    entry_id: int,
    force=False,
    deletion_msg="",
    prompt=True,
) -> bool:
    if is_deleted(entry_type, entry_id):
        logger.warning(f"Entry {entry_id} has already been deleted.")
        return False

    assert entry_type in get_args(EntryType), "Invalid entry type"  # noqa: S101
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


def get_entry_link(entry_type: EntryType, entry_id: int) -> str:
    if entry_type == "User":
        username = get_username_by_id(entry_id)
        return f"{WEBSITE}/Profile/{username}"
    return f"{WEBSITE}/{entry_type_to_url[entry_type]}/{entry_id}"


def get_entry_from_link(entry_link: str) -> Entry:
    # https://vocadb.net/S/83619
    # --> ("Song", 83619)
    link = entry_link.split(WEBSITE + "/")[1]
    if "venue" in link.lower():
        entry_id = int(link.split("/")[2])
        return ("Venue", entry_id)

    entry_type_slug, entry_id_str, *_ = link.split("/")
    entry_type = entry_url_to_type[entry_type_slug]
    return (entry_type, int(entry_id_str))


def search_entry(name: str, entry_type: EntryType, max_results=3) -> str:
    search_functions: dict[EntryType, tuple[Callable[..., tuple[list, int]], str]] = {
        "Song": (get_songs_with_total_count, "RatingScore"),
        "Album": (get_albums_with_total_count, "CollectionCount"),
        "Artist": (get_artists_with_total_count, "FollowerCount"),
        "Tag": (get_tags_with_total_count, "UsageCount"),
        "SongList": (get_featured_songlists_with_total_count, "None"),
        "Venue": (get_venues_with_total_count, "None"),
        "ReleaseEvent": (get_events_with_total_count, "None"),
        "ReleaseEventSeries": (get_many_series_with_total_count, "None"),
        "User": (get_users_with_total_count, "RegisterDate"),
    }

    params = {
        "nameMatchMode": "Exact",
        "getTotalCount": True,
        "query": name,
    }
    search_function, sort_rule = search_functions[entry_type]
    params["sort"] = sort_rule
    results, total_count = search_function(params, max_results=max_results)
    if not results or total_count > 1:
        params["nameMatchMode"] = "Partial"
        results, total_count = search_function(params, max_results=max_results)
    if not results:
        return f"No results found for '{name}'"

    links = [
        get_entry_link(entry_type, entry["id"])  # type: ignore
        for entry in results[:max_results]  # type: ignore
    ]

    if len(links) == 1:
        return links[0]

    bullet_point_links = [f"- {link}" for link in links]
    if total_count > max_results:
        bullet_point_links.append("- ...")

    return f"Found {total_count} entries for '{name}':\n{'\n'.join(bullet_point_links)}"
