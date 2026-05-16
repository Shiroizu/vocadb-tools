from typing import Literal

from vdbpy.types.changed_fields import (
    ChangedFields,
)
from vdbpy.types.shared import (
    BaseEntryVersion,
    EntryType,
)
from vdbpy.types.songs import SongVersion
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CorrectEditCheckTestResult,
    CorrectEntryCheckTestResult,
    CorrectTestResults,
    RuleModuleResult,
)

logger = get_logger()

MSG = "Do not add direct download links."
FIELDS: list[ChangedFields] = ["Lyrics", "WebLinks"]
ENTRY_TYPES: list[EntryType] = []  # Check all entry types
COMPLETE = False
AUTOMATICALLY_FIXED: bool | Literal["Partially"] = False

domains = [
    "dropbox.com",
    "mediafire.com",
    "dropboxusercontent.com",
    "drive.google.com",
    "onedrive.live.com",
    "axfc.net",
    "4shared.com",
    "mega.co.nz",
    "mega.nz",
]


def check_entry_version_for_rule(version_data: BaseEntryVersion) -> RuleModuleResult:
    all_link_urls: list[str] = []
    for link in version_data.external_links:
        all_link_urls.append(link.url)

    if isinstance(version_data, SongVersion):
        for lyrics in version_data.lyrics:
            all_link_urls.append(lyrics.url)

    if not all_link_urls:
        return "Not applicable"

    for link in all_link_urls:
        for domain in domains:
            if domain in link:
                return "Rule violation"

    return "Valid"


def test() -> CorrectTestResults:
    edit_check_tests: CorrectEditCheckTestResult = {
        "Valid": [
            ("Song", 889898, 3020461), # External link
            ("Song", 889898, 3034077), # Lyrics
            ("Album", 51672, 271686),
            ("Artist", 72959, 598870), # Regular artist
            ("Artist", 72959, 598874), # Original voicebank
            ("Artist", 72959, 598880), # Derived voicebank
            ("ReleaseEvent", 9772, 41635), # Standalone event
            ("ReleaseEvent", 9772, 41639), # Series event
            ("ReleaseEventSeries", 1041, 3837),
            ("Tag", 6366, 57269),
            ("Venue", 433, 1115),
        ],
        "Rule violation": [
            ("Song", 889898, 3034099), # External link
            ("Song", 889898, 3020446), # Lyrics
            ("Album", 51672, 271684),
            ("Artist", 72959, 598868), # Regular artist
            ("Artist", 72959, 598872), # Original voicebank
            ("Artist", 72959, 598878), # Derived voicebank
            ("ReleaseEvent", 9772, 41633), # Standalone event
            ("ReleaseEvent", 9772, 41637), # Series event
            ("ReleaseEventSeries", 1041, 3835),
            ("Tag", 6366, 57267),
            ("Venue", 433, 1116),
        ],
        "Not applicable": [
            ("Song", 889898, 3020191),
            ("Album", 51672, 271685),
            ("Artist", 72959, 598869), # Regular artist
            ("Artist", 72959, 598873), # Original voicebank
            ("Artist", 72959, 598879), # Derived voicebank
            ("ReleaseEvent", 9772, 41634), # Standalone event
            ("ReleaseEvent", 9772, 41638), # Series event
            ("ReleaseEventSeries", 1041, 3836),
            ("Tag", 6366, 57268),
            ("Venue", 433, 1106),
        ],
    }
    entry_check_tests: CorrectEntryCheckTestResult = {
        "Valid": [
            (3020461, 329, ("Song", 889898, 3020461)),
            (271686, 31074, ("Album", 51672, 271686)),
            (598870, 31074, ("Artist", 72959, 598870)),
            (41635, 31074, ("ReleaseEvent", 9772, 41635)),
            (3837, 31074, ("ReleaseEventSeries", 1041, 3837)),
            (57269, 31074, ("Tag", 6366, 57269)),
            (1115, 31074, ("Venue", 433, 1115)),
        ],
        "Rule violation": [
            (3020446, 329, ("Song", 889898, 3020446)),
            (271684, 31074, ("Album", 51672, 271684)),
            (598872, 31074, ("Artist", 72959, 598872)),
            (41633, 31074, ("ReleaseEvent", 9772, 41633)),
            (3835, 31074, ("ReleaseEventSeries", 1041, 3835)),
            (57267, 31074, ("Tag", 6366, 57267)),
            (1116, 31074, ("Venue", 433, 1116)),
        ],
        "Not applicable": [
            (3020190, 329, ("Song", 889898, 3020190)),
            (271685, 31074, ("Album", 51672, 271685)),
            (598879, 31074, ("Artist", 72959, 598879)),
            (41638, 31074, ("ReleaseEvent", 9772, 41638)),
            (3836, 31074, ("ReleaseEventSeries", 1041, 3836)),
            (57268, 31074, ("Tag", 6366, 57268)),
            (1106, 31074,("Venue", 433, 1106)),
        ],
    }
    return edit_check_tests, entry_check_tests
