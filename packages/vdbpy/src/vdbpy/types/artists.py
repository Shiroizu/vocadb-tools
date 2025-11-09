from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from vdbpy.types.shared import BaseEntry, BaseEntryVersion, EntryStatus, Picture

VoicebankType = Literal[
    "Vocaloid",
    "UTAU",
    "CeVIO",
    "OtherVoiceSynthesizer",
    "SynthesizerV",
    "NEUTRINO",
    "VoiSona",
    "NewType",
    "Voiceroid",
    "VOICEVOX",
    "ACEVirtualSinger",
    "AIVOICE",
]  # no 'type' for get_args() support

BasicArtistType = Literal[
    "Unknown",
    "Circle",
    "Label",
    "OtherGroup",
    "Producer",
    "Animator",
    "Illustrator",
    "Lyricist",
    "OtherVocalist",
    "OtherIndividual",
    "CoverArtist",
    "Instrumentalist",
]  # no 'type' for get_args() support
# Skipped: "Utaite", "Band", "Vocalist", "Character", "Designer"

# -------------------- types -------------------- #

type ArtistParticipationStatus = Literal[
    "Everything", "OnlyMainAlbums", "OnlyCollaborations"
]

type ArtistType = VoicebankType | BasicArtistType

type ArtistRole = Literal[
    "Default",
    "Other",
    "Animator",
    "Arranger",
    "Composer",
    "Distributor",
    "Illustrator",
    "Instrumentalist",
    "Lyricist",
    "Mastering",
    "Publisher",
    "Vocalist",
    "VoiceManipulator",
    "Mixer",
    "VocalDataProvider",
]  # "Chorus", "Encoder",

type ArtistRoleCategory = Literal[
    "Nothing",
    "Vocalist",
    "Producer",
    "Animator",
    "Label",
    "Circle",
    "Other",
    "Illustrator",
    # "Band",
    # "Subject",
]

# -------------------- dataclasses -------------------- #


@dataclass
class Artist:
    additional_names: str
    artist_type: ArtistType
    deleted: bool
    artist_id: int
    name: str
    picture_mime: str
    release_date: datetime | None
    version_count: int
    status: EntryStatus


@dataclass
class ArtistVersion(BaseEntryVersion):
    # https://vocadb.net/api/artists/versions/x -> versions -> firstData
    # Skipped fields:
    # - mainPictureMime
    # - members
    artist_type: ArtistType
    group_ids: list[int]
    vb_voice_provider_ids: list[int]
    vb_manager_ids: list[int]
    vb_illustrator_ids: list[int]
    vb_chara_designer_ids: list[int]
    vb_base_id: int
    vb_release_date: datetime | None
    additional_pictures: list[Picture]


@dataclass
class ArtistParticipation:
    # api/songs?fields=Artists
    """
    "artist": {
        "additionalNames": "string",
        "artistType": "Unknown",
        "deleted": true,
        "id": 0,
        "name": "string",
        "pictureMime": "string",
        "releaseDate": "2025-11-08T07:48:57.066Z",
        "status": "Draft",
        "version": 0
    },
    "effectiveRoles": "Default",
    "id": 0,
    "name": "string",
    "roles": "Default"
    """

    artist: Artist
    categories: list[ArtistRoleCategory]
    effective_roles: list[ArtistRole]
    participation_id: int
    name: str
    is_support: bool
    specified_roles: list[ArtistRole]
    # is_custom_name: bool


@dataclass
class OptionalArtistFields:
    pass  # TODO implement


@dataclass
class ArtistEntry(BaseEntry, OptionalArtistFields):
    pass  # TODO implement
