from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.tags import Tag, TagRelation, TagVersion


def parse_tag_version(data: dict[Any, Any]) -> TagVersion:
    base_entry_version = parse_base_entry_version(data)

    def parse_tag_relation(data: dict[Any, Any]) -> TagRelation:
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


def parse_tag(data: dict[Any, Any]) -> Tag:
    data = data["tag"]  # skip "count"
    return Tag(
        additional_names=data.get("additionalNames", ""),
        category=data.get("categoryName", ""),
        tag_id=data["id"],
        name=data["name"],
        url_slug=data["urlSlug"],
    )
