"""Types for revision diffing."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from vdbpy.types.shared import EditType, EntryStatus, EntryType
from vdbpy.types.versions import EntryVersion

type Verb = Literal["added", "updated", "removed", "reordered"]

EMPTY_DISPLAY = "-"


@dataclass(frozen=True)
class FieldSpec:
    """How to extract, compare and render one field of a version state."""

    key: str
    label: str
    changed_field: str
    empty: Any = ""
    extract: Callable[[EntryVersion], Any] | None = None
    render: Callable[[Any], str] | None = None
    details: Callable[[Any, Any], list[str]] | None = None
    full_diff: Callable[[Any, Any], list[tuple[str, str]]] | None = None
    source_keys: tuple[str, ...] = ()

    def get(self, state: EntryVersion | None) -> Any:
        if state is None:
            return self.empty
        value = self.extract(state) if self.extract else getattr(state, self.key, None)
        return self.empty if value is None else value

    def show(self, value: Any) -> str:
        if self.is_empty(value):
            return EMPTY_DISPLAY
        return self.render(value) if self.render else str(value)

    def is_empty(self, value: Any) -> bool:
        return value == self.empty

    def claimed_keys(self) -> tuple[str, ...]:
        return self.source_keys or (self.key,)


@dataclass(frozen=True)
class FieldChange:
    key: str
    label: str
    verb: Verb
    before: str
    after: str
    changed_field: str | None = None
    specced: bool = True
    details: list[str] = field(default_factory=list)
    full_diffs: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class VersionDiff:
    entry_type: EntryType
    entry_id: int
    version_id: int
    version_number: int
    edit_date: datetime
    edit_event: EditType
    author_id: int
    author_name: str
    update_notes: str
    reported_changed_fields: list[str]
    changes: list[FieldChange] = field(default_factory=list)
    status: EntryStatus | None = None
    previous_status: EntryStatus | None = None
    data_available: bool = True
    baseline_version_number: int | None = None
    entry_version_count: int | None = None  # all versions, shown or not

    @property
    def is_creation(self) -> bool:
        return self.edit_event == "Created"

    @property
    def baseline_is_stale(self) -> bool:
        """True when hidden versions sit between the baseline and this one."""
        baseline = (
            -1 if self.baseline_version_number is None else self.baseline_version_number
        )
        return baseline != self.version_number - 1

    @property
    def status_changed(self) -> bool:
        return self.previous_status is not None and self.previous_status != self.status

    @property
    def detected_changed_fields(self) -> set[str]:
        detected = {
            change.changed_field for change in self.changes if change.changed_field
        }
        if self.status_changed:
            detected.add("Status")
        return detected
