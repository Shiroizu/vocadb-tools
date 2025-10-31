from vdbpy.types.entry_versions import (
    PV,
    ArtistParticipation,
    BaseEntryVersion,
    EventParticipation,
    ExternalLink,
    Picture,
)
from vdbpy.utils.date import parse_date


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
                name=pv.get("name", ""),
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
