from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.tags import Tag, TagRelation, TagVersion


def parse_tag_relation(data: dict[Any, Any]) -> TagRelation:
    return TagRelation(
        tag_id=data["id"],
        name_hint=data["nameHint"],
    )


def parse_tag_version(data: dict[Any, Any]) -> TagVersion:
    version_data = data["versions"]["firstData"]
    return TagVersion(
        tag_category=version_data.get("categoryName", ""),
        hidden_from_suggestions=version_data.get("hideFromSuggestions", False),
        parent_tag=parse_tag_relation(version_data["parent"])
        if "parent" in version_data
        else None,
        related_tags=[parse_tag_relation(tag) for tag in version_data["relatedTags"]]
        if "relatedTags" in version_data
        else [],
        **parse_base_entry_version(data).__dict__,
    )


def parse_tag(data: dict[Any, Any]) -> Tag:
    data = data["tag"]  # skip "count"
    return Tag(
        additional_names=data.get("additionalNames", ""),
        category=data.get("categoryName", ""),
        tag_id=data["id"],
        name=data["name"],
        url_slug=data["urlSlug"],
    )
