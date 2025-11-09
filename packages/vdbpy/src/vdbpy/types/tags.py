from dataclasses import dataclass
from typing import Literal

from vdbpy.types.shared import BaseEntry, BaseEntryVersion

type TagCategory = Literal[
    "Genres",
    "Animation",
    "Composition",
    "Copyrights",
    "Derivative",
    "Distribution",
    "Event",
    "Games",
    "Instruments",
    "Jobs",
    "Languages",
    "Lyrics",
    "Media",
    "MMD Models",
    "Series",
    "Sources",
    "Subjective",
    "Themes",
    "Vocalists",
]


@dataclass
class TagRelation:
    tag_id: int
    name_hint: str


@dataclass
class TagVersion(BaseEntryVersion):
    # https://vocadb.net/api/tags/versions/x -> versions -> firstData
    # Missing/unsupported fields:
    # - targets (new & old)
    tag_category: TagCategory | str
    hidden_from_suggestions: bool
    parent_tag: TagRelation | None
    related_tags: list[TagRelation]


@dataclass
class OptionalTagFields:
    pass  # TODO implement


@dataclass
class TagEntry(BaseEntry, OptionalTagFields):
    pass  # TODO implement


@dataclass
class Tag:
    additional_names: str
    category: TagCategory
    tag_id: int
    name: str
    url_slug: str
