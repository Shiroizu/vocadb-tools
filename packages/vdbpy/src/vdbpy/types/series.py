from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vdbpy.types.events import EventCategory

from vdbpy.types.shared import BaseEntry, BaseEntryVersion

type ReleaseEventSeriesEntry = dict[Any, Any]  # TODO implement


@dataclass
class ReleaseEventSeriesVersion(BaseEntryVersion):
    autofilled_names: tuple[str, str, str] | None
    event_category: "EventCategory"


@dataclass
class EventSeriesRelation:
    series_id: int
    name_hint: str


@dataclass
class OptionalReleaseEventSereisFields:
    pass  # TODO implement


@dataclass
class ReleaseEventSeries(BaseEntry, OptionalReleaseEventSereisFields):
    pass  # TODO implement
