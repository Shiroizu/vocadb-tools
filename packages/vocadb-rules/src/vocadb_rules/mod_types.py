from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

# TODO: move to VDBPY
from vdbpy.types.changed_fields import ChangedFields
from vdbpy.types.events import ReleaseEventVersion
from vdbpy.types.series import ReleaseEventSeriesVersion
from vdbpy.types.shared import (
    BaseEntryVersion,
    EntryId,
    EntryStatus,
    EntryTuple,
    EntryType,
    UserEdit,
    UserId,
    VersionId,
    VersionTuple,
)
from vdbpy.types.venues import VenueVersion

if TYPE_CHECKING:
    from vdbpy.utils.dump import Dump

type RuleId = int
type ReportId = int
type ReportType = Literal[
    "InvalidInfo",
    "Duplicate",
    "Inappropriate",
    "Other",
    "InvalidTag",
    "BrokenPV",
]


@dataclass
class RuleTableRow:
    rule_name: str
    rule_entry_types_strings: list[str]
    rule_entry_status: EntryStatus
    rule_tag_id: int
    rule_mikumodded: bool | Literal["Planned"]
    rule_complete: bool
    rule_autofixed: bool | Literal["Partially"]


@dataclass
class EntryReport:
    report_id: ReportId
    entry_type: EntryType
    entry_id: EntryId
    date: datetime
    report_type: ReportType
    notes: str
    author: str | None


SavedEditCheckResult = Literal[
    "Valid",
    "Not applicable",
    "Rule violation",
    "Possible rule violation",
]
EditCheckResult = Literal[SavedEditCheckResult, "Unrelated fields", "No data"]

RuleModuleResult = Literal[SavedEditCheckResult, "Wrong entry type"]

SavedEntryCheckResult = Literal[
    SavedEditCheckResult,
    "Deleted",
    "Too old",
    "No autofix",
]
type CheckResult = Literal[SavedEntryCheckResult, "Wrong entry type", "No data"]

type EntryWithVersionIds = tuple[EntryTuple, VersionId, VersionId]
type RuleModules = dict[RuleId, tuple[str, ModuleType]]

type ReportWithVersionIdAndRelevantEntries = tuple[
    EntryReport,
    VersionId,
    list[EntryTuple],
]
type ParsedReports = list[ReportWithVersionIdAndRelevantEntries]
type ParsedReportsByRuleId = dict[RuleId, ParsedReports]
type MikuModReports = dict[UserId, ParsedReportsByRuleId]

type EntriesBySavedEditCheckResult = dict[SavedEditCheckResult, set[EntryTuple]]
type EditCheckMemory = dict[RuleId, EntriesBySavedEditCheckResult]

type ReportsToSend = dict[UserId, dict[RuleId, tuple[str, list[EntryWithVersionIds]]]]
type EntriesByRuleId = dict[RuleId, set[EntryTuple]]

type EntryCheckData = tuple[VersionId, CheckResult, VersionId, UserId]
type EntryCheckMemory = dict[
    RuleId,
    dict[EntryTuple, EntryCheckData],
]

type CorrectEditCheckTestResult = dict[RuleModuleResult, list[VersionTuple]]
type CorrectEntryCheckTestResult = dict[
    CheckResult,
    list[tuple[VersionId, UserId, VersionTuple]],
]
type CorrectTestResults = tuple[CorrectEditCheckTestResult, CorrectEntryCheckTestResult]

StatColumns = Literal[
    "Valid",
    "Rule violation",
    "Possible rule violation",
    "Not applicable",
    "No autofix",
]
type EntryCheckStatsByRuleId = dict[RuleId, dict[EntryTuple, StatColumns]]
type EditByEntryTypeAndId = dict[EntryType, dict[EntryId, UserEdit]]

EntryTypesWithoutVersionedStatus = (
    ReleaseEventVersion,
    ReleaseEventSeriesVersion,
    VenueVersion,
)


@runtime_checkable
class RuleModule(Protocol):
    MSG: str
    FIELDS: list[ChangedFields]
    ENTRY_TYPES: list[EntryType] | Literal["All"]
    COMPLETE: bool
    AUTOMATICALLY_FIXED: bool | Literal["Partially"]

    def check_entry_version_for_rule(
        self,
        version_data: BaseEntryVersion,
    ) -> RuleModuleResult: ...

    def test(self) -> CorrectTestResults: ...


@runtime_checkable
class AutofixableRuleModule(RuleModule, Protocol):
    """Rule modules that declare AUTOMATICALLY_FIXED in (True, "Partially")."""

    autofix: Callable[..., bool]


@runtime_checkable
class TaggedRuleModule(RuleModule, Protocol):
    """Rule modules that scope their check to entries carrying a specific tag."""

    TAG_ID: int

    def find_relevant_entries(self, save_dir: Path) -> set[EntryTuple]: ...


@runtime_checkable
class DumpRuleModule(Protocol):
    MSG: str
    ENTRY_TYPES: list[EntryType] | Literal["All"]
    COMPLETE: bool
    AUTOMATICALLY_FIXED: bool | Literal["Partially"]

    def analyze_dump(self, dump: Dump) -> set[EntryTuple]: ...

    def test(self) -> CorrectTestResults: ...
