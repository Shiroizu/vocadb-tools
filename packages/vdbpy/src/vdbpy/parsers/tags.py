from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.entry_versions import TagRelation, TagVersion


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
