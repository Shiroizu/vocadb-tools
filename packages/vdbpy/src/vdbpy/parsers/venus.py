from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.venues import VenueVersion


def parse_venue_version(data: dict[Any, Any]) -> VenueVersion:
    version_data = data["versions"]["firstData"]

    coordinates = version_data.get("coordinates", {})
    return VenueVersion(
        address=version_data.get("address"),
        country_code=version_data.get("addressCountryCode"),
        latitude=coordinates.get("latitude", None),
        longitude=coordinates.get("longitude", None),
        **parse_base_entry_version(data).__dict__,
    )
