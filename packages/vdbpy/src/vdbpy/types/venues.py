from dataclasses import dataclass

from vdbpy.types.shared import BaseEntry, BaseEntryVersion


@dataclass
class VenueVersion(BaseEntryVersion):
    address: str | None
    country_code: str | None
    latitude: float | None
    longitude: float | None


@dataclass
class VenueRelation:
    venue_id: int
    name_hint: str


@dataclass
class OptionalVenueFields:
    pass  # TODO implement


@dataclass
class VenueEntry(BaseEntry, OptionalVenueFields):
    pass  # TODO implement
