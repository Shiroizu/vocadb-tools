from typing import Any, Literal

import requests
from vdbpy.edit.entries import edit_entry
from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import BaseEntryVersion, EntryTuple, EntryType
from vdbpy.types.songs import SongVersion
from vdbpy.utils.console import get_boolean
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Always prefer adding the desktop version of the link."
FIELDS: list[ChangedFields] = ["Lyrics", "WebLinks"]
ENTRY_TYPES: list[EntryType] = []
COMPLETE = False
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = "Partially"

# TODO move to a config file
SAFE_DOMAINS_TO_EDIT = ["youtube", "vk", "soundcloud", "twitter", "facebook", "twitch"]
UNSAFE_DOMAINS_TO_EDIT = ["ykimg", "seiga"]


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    all_link_urls: list[str] = []
    for link in version_data.external_links:
        all_link_urls.append(link.url)

    if isinstance(version_data, SongVersion):
        for lyrics in version_data.lyrics:
            all_link_urls.append(lyrics.url)

    if not all_link_urls:
        return "Not applicable"

    mobile_subdomains = ["m", "sp", "mobile"]

    for url in all_link_urls:
        if not url.strip():
            continue
        trimmed = url.removeprefix("http")
        trimmed = trimmed.removeprefix("s")
        trimmed = trimmed.removeprefix("://")
        trimmed = trimmed.removeprefix("www.")
        try:
            subdomain, domain, *_ = trimmed.split(".")
            if domain in UNSAFE_DOMAINS_TO_EDIT:
                continue
            if subdomain in mobile_subdomains:
                return "Rule violation"
        except ValueError:
            logger.warning(f"   Malformatted url '{trimmed}'")
            continue

    return "Valid"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Artist", 72959, 571061),
            ("Artist", 126348, 582588),
            ("Song", 889898, 3031669),
            ("Album", 51672, 271513),
            ("Tag", 6366, 57221),
            ("ReleaseEvent", 9772, 41598), # series
            ("ReleaseEvent", 9772, 41604), # standalone
            ("ReleaseEventSeries", 1041, 3825),
            ("Venue", 433, 1115),
        ],
        "Not applicable": [
            ("Artist", 72959, 571066),
            ("Song", 889898, 3031665),
            ("Album", 51672, 271518),
            ("Tag", 6366, 57225),
            ("ReleaseEvent", 9772, 41602), # series
            ("ReleaseEvent", 9772, 41608), # standalone
            ("ReleaseEventSeries", 1041, 3829),
            ("Venue", 433, 1106),
        ],
        "Rule violation": [
            ("Artist", 72959, 571065),
            ("Artist", 72959, 571064),
            ("Artist", 72959, 571063),
            ("Song", 889898, 3031674),
            ("Song", 889898, 3031683),
            ("Song", 889898, 3031686),
            ("Album", 51672, 271515),
            ("Album", 51672, 271516),
            ("Album", 51672, 271517),
            ("Tag", 6366, 57222),
            ("Tag", 6366, 57223),
            ("Tag", 6366, 57224),
            ("ReleaseEvent", 9772, 41599), # series
            ("ReleaseEvent", 9772, 41600), # series
            ("ReleaseEvent", 9772, 41601), # series
            ("ReleaseEvent", 9772, 41605), # standalone
            ("ReleaseEvent", 9772, 41606), # standalone
            ("ReleaseEvent", 9772, 41607), # standalone
            ("ReleaseEventSeries", 1041, 3826),
            ("ReleaseEventSeries", 1041, 3827),
            ("ReleaseEventSeries", 1041, 3828),
            ("Venue", 433, 1112),
            ("Venue", 433, 1113),
            ("Venue", 433, 1114),
        ],
    }

    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [
            (582588, 26517, ("Artist", 126348, 582588)),
            (3031669, 31074, ("Song", 889898, 3031669)),
            (271513, 31074, ("Album", 51672, 271513)),
            (57221, 31074, ("Tag", 6366, 57221)),
            (41598, 31074, ("ReleaseEvent", 9772, 41598)), # series
            (41604, 31074, ("ReleaseEvent", 9772, 41604)), # standalone
            (3825, 31074, ("ReleaseEventSeries", 1041, 3825)),
            (1115, 31074, ("Venue", 433, 1115)),
        ],
        "Not applicable": [
            (571066, 329, ("Artist", 72959, 571066)),
            (3031665, 31074, ("Song", 889898, 3031665)),
            (271518, 31074, ("Album", 51672, 271518)),
            (57225, 31074, ("Tag", 6366, 57225)),
            (41602, 31074, ("ReleaseEvent", 9772, 41602)), # series
            (41608, 31074, ("ReleaseEvent", 9772, 41608)), # standalone
            (3829, 31074, ("ReleaseEventSeries", 1041, 3829)),
            (1106, 31074, ("Venue", 433, 1106)),
        ],
        "Rule violation": [
            (571063, 329, ("Artist", 72959, 571063)),
            (3031674, 31074, ("Song", 889898, 3031674)),
            (271515, 31074, ("Album", 51672, 271515)),
            (57222, 31074, ("Tag", 6366, 57222)),
            (41599, 31074, ("ReleaseEvent", 9772, 41599)), # series
            (41605, 31074, ("ReleaseEvent", 9772, 41605)), # standalone
            (3826, 31074, ("ReleaseEventSeries", 1041, 3826)),
            (1112, 31074, ("Venue", 433, 1112)),
        ],
    }
    return edit_check_tests, entry_check_tests


def fix_mobile_url(url: str) -> str:
    mobile_subdomains = ["m", "sp", "mobile"]
    trimmed = url.removeprefix("http")
    trimmed = trimmed.removeprefix("s")
    trimmed = trimmed.removeprefix("://")
    trimmed = trimmed.removeprefix("www.")
    try:
        subdomain, domain, *_ = trimmed.split(".")
    except ValueError:
        logger.warning(f"   Malformatted url '{trimmed}'")
        return url

    if trimmed.startswith("m.bilibili.com/space/"):
        return url.replace("m.bilibili.com/space/", "space.bilibili.com/").split("?")[0]
    if subdomain in mobile_subdomains:
        if subdomain == "sp" and domain == "nicovideo":
            if "/my/" in url:
                logger.warning("Incorrect nico link format (includes /my/)")
                return url
            return url.replace("sp.", "www.").split("?")[0]
        if subdomain == "m" and domain == "bilibili":
            return url.replace("://m.", "://www.")

        if domain in UNSAFE_DOMAINS_TO_EDIT:
            return url
        fixed_url = url.replace(f"{subdomain}.", "")
        if domain not in SAFE_DOMAINS_TO_EDIT:
            logger.warning(f"Found unsafe domain '{domain}' to edit for link '{url}'")
            link_works = get_boolean(f"Does '{fixed_url}' work?")
            if link_works:
                logger.warning(f"Add domain '{domain}' to SAFE_DOMAINS_TO_EDIT")
                return fixed_url
            return url
        return fixed_url
    return url


def autofix(
    session: requests.Session,
    entry: EntryTuple,
    base_update_note: str = "",
    prompt: bool = True,
    args: Any = None,
) -> bool:
    return edit_entry(
        session=session,
        entry=entry,
        edit_function=fix_mobile_links,
        prompt=prompt,
        base_update_note=base_update_note,
        args=args,
    )


def fix_mobile_links(
    data: dict[Any, Any], base_update_note: str = "", args: Any = None,
) -> dict[Any, Any]:
    # TODO full tests
    # "lyrics": [
    #     {
    #         "isNew": false,
    #         "cultureCodes": ["fr"],
    #         "source": "test lyrics url source",
    #         "translationType": "Original",
    #         "url": "test lyrics url",
    #         "value": "test lyrics",
    #     }
    # ],
    # "webLinks": [
    #     {
    #        "id": 197376,
    #        "category": "Commercial",
    #        "description": "external link description",
    #        "disabled": true,
    #        "url": "external link url",
    #    }
    # ],

    temp_notes: list[str] = []
    lyrics_and_external_links = {
        "lyrics": data.get("lyrics", []),
        "webLinks": data.get("webLinks", []),
    }

    fix_count: int = 0
    for field_name, obj in lyrics_and_external_links.items():
        if not obj:
            continue
        fixed_data: list[dict[Any, Any]] = []
        for item in obj:
            url = str(item.get("url", "")).strip()
            if url:
                fixed = fix_mobile_url(url)
                if fixed != url:
                    item["url"] = fixed
                    fix_count += 1
                    temp_notes.append(f"'{url}' -> '{fixed}'")
            fixed_data.append(item)
        data[field_name] = fixed_data

    if not fix_count:
        return {}

    update_notes = f"Fixed {fix_count} mobile url(s): " + ", ".join(temp_notes)
    data["updateNotes"] = base_update_note + update_notes

    return data
