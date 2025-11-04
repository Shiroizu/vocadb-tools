from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.entry_versions import VenueVersion


def parse_venue_version(data: dict[Any, Any]) -> VenueVersion:
    data, base_entry_version = parse_base_entry_version(data)
    autofilled_names = (
        data["translatedName"].values()
        if "names" not in data and "translatedName" in data
        else None
    )

    coordinates = data.get("coordinates", {})
    return VenueVersion(
        autofilled_names=autofilled_names,
        address=data.get("address", None),
        country_code=data.get("addressCountryCode", None),
        latitude=coordinates.get("latitude", None),
        longitude=coordinates.get("longitude", None),
        **base_entry_version.__dict__,
    )
