from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version, parse_pictures
from vdbpy.types.artists import Artist, ArtistParticipation, ArtistVersion
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger

logger = get_logger()


def parse_groups(data: dict[Any, Any]) -> dict[str, list[int]]:
    group_link_types = [
        "CharacterDesigner",
        "Group",
        "Illustrator",
        "Manager",
        "VoiceProvider",
    ]
    group_ids_by_link_type: dict[str, list[int]] = {
        group_link_type: [] for group_link_type in group_link_types
    }
    for group in data["groups"]:
        link_type = group["linkType"]
        if link_type not in group_link_types:
            logger.warning(f"Unknown link type '{link_type} for Ar/{data['id']}")
        group_ids_by_link_type[link_type].append(group["id"])
    return group_ids_by_link_type


def parse_artist_version(data: dict[Any, Any]) -> ArtistVersion:
    version_data = data["versions"]["firstData"]
    groups_by_link_type = parse_groups(version_data)
    return ArtistVersion(
        additional_pictures=parse_pictures(version_data["pictures"])
        if "pictures" in version_data
        else [],
        artist_type=version_data["artistType"],
        group_ids=groups_by_link_type["Group"],
        vb_base_id=version_data["baseVoicebank"]["id"]
        if "baseVoicebank" in version_data
        else 0,
        vb_chara_designer_ids=groups_by_link_type["CharacterDesigner"],
        vb_illustrator_ids=groups_by_link_type["Illustrator"],
        vb_manager_ids=groups_by_link_type["Manager"],
        vb_voice_provider_ids=groups_by_link_type["VoiceProvider"],
        vb_release_date=parse_date(version_data["releaseDate"])
        if "releaseDate" in version_data
        else None,
        **parse_base_entry_version(data).__dict__,
    )


def parse_artist(data: dict[Any, Any]) -> Artist:
    return Artist(
        additional_names=data.get("additionalNames", ""),
        artist_type=data["artistType"],
        deleted=data["deleted"],
        artist_id=data["id"],
        name=data["name"],
        picture_mime=data.get("pictureMime", ""),
        release_date=parse_date(data["releaseDate"]) if "releaseDate" in data else None,
        version_count=data["version"],
        status=data["status"],
    )


def parse_artist_participation(data: dict[Any, Any]) -> list[ArtistParticipation]:
    # api/songs?fields=Artists
    # TODO verify same structure for other entry types

    return [
        ArtistParticipation(
            entry=parse_artist(artist["artist"])
            if "artist" in artist
            else "Custom artist",
            categories=artist["categories"].split(", "),
            effective_roles=artist["effectiveRoles"],
            participation_id=artist["id"],
            name=artist["name"],
            is_support=artist["isSupport"],
            specified_roles=artist["roles"],
        )
        for artist in data
    ]
