from typing import Any

from vdbpy.types.shared import (
    PV,
    BaseEntry,
    BaseEntryVersion,
    DefaultLanguage,
    ExternalLink,
    Picture,
    VersionArtistParticipation,
)
from vdbpy.utils.date import parse_date


def parse_version_names(data: dict[Any, Any]) -> tuple[str, str, str, list[str]]:
    if "names" in data:
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
                case _:
                    msg = f"Unexpected language {language}"
                    raise ValueError(msg)

        return name_non_english, name_romaji, name_english, aliases

    if "translatedName" in data:
        return (
            data["translatedName"]["japanese"],
            data["translatedName"]["romaji"],
            data["translatedName"]["english"],
            [],
        )

    msg = f"No names found: {data}"
    raise ValueError(msg)


def parse_names(data: dict[Any, Any]) -> tuple[dict[DefaultLanguage, str], list[str]]:
    names: dict[DefaultLanguage, str] = {}
    aliases: list[str] = []

    for entry in data:
        language = entry["language"]
        value = entry["value"]
        match language:
            case "Japanese":
                names["Non-English"] = value
            case "Romaji":
                names["Romaji"] = value
            case "English":
                names["English"] = value
            case "Unspecified":
                aliases.append(value)
            case _:
                msg = f"Unexpected language {language}"
                raise ValueError(msg)

    return names, aliases


def parse_version_artist_participation(
    data: dict[Any, Any],
) -> list[VersionArtistParticipation]:
    return [
        VersionArtistParticipation(
            is_supporting=artist_participation["isSupport"],
            artist_id=artist_participation["id"],
            roles=artist_participation["roles"].split(", "),
            name_hint=artist_participation["nameHint"],
        )
        for artist_participation in data
    ]


def parse_pvs(data: dict[Any, Any]) -> list[PV]:
    return [
        PV(
            author=pv["author"],
            disabled=pv["disabled"],
            length=pv["length"],
            name=pv.get("name", ""),
            pv_id=pv["pvId"],
            pv_service=pv["service"],
            pv_type=pv["pvType"],
            publish_date=parse_date(pv["publishDate"]) if "publishDate" in pv else None,
        )
        for pv in data
    ]


def parse_links(data: dict[Any, Any]) -> list[ExternalLink]:
    raw_links: list[Any] = []
    if "externalLinks" in data:
        raw_links = data["externalLinks"]
    elif "webLinks" in data:  # inconsistent naming
        raw_links = data["webLinks"]

    if not raw_links:
        return []

    return [
        ExternalLink(
            category=link["category"],
            description=link["description"],
            disabled=link["disabled"],
            url=link["url"],
        )
        for link in raw_links
    ]


def parse_pictures(data: dict[Any, Any]) -> list[Picture]:
    return [
        Picture(
            picture_id=picture["id"],
            mime=picture["mime"],
            name=picture["name"],
        )
        for picture in data
    ]


def parse_base_entry_version(
    data: dict[Any, Any],
) -> BaseEntryVersion:
    entry_status = data["archivedVersion"]["status"]
    data = data["versions"]["firstData"]

    name_non_english, name_romaji, name_english, aliases = parse_version_names(data)
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

    return BaseEntryVersion(
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


def parse_base_entry(data: dict[Any, Any]) -> BaseEntry:
    return BaseEntry(
        id=data["id"],
        deleted=data.get("deleted", False),
        create_date=parse_date(data["createDate"]),
        default_name=data["defaultName"],
        default_name_language="Non-English"
        if data["defaultNameLanguage"] == "Japanese"
        else data["defaultNameLanguage"],
        version_count=data["version"],
        status=data["status"],
    )


def parse_event_ids(data: dict[Any, Any]) -> list[int]:
    event_ids: set[int] = set()
    # https://vocadb.net/api/albums/versions/256441
    # https://vocadb.net/api/albums/versions/158700

    original_release = data.get("originalRelease", data)
    release_event = original_release.get("releaseEvent", {})
    if release_event:
        event_ids.add(release_event["id"])
    release_events = original_release.get("releaseEvents", [])
    if release_events:
        for event in release_events:
            event_ids.add(event["id"])
    return list(event_ids)
