from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.entry_versions import ReleaseEventSeriesVersion


def parse_release_event_series_version(
    data: dict[Any, Any],
) -> ReleaseEventSeriesVersion:
    data, base_entry_version = parse_base_entry_version(data)
    autofilled_names = (
        data["translatedName"].values()
        if "names" not in data and "translatedName" in data
        else None
    )

    return ReleaseEventSeriesVersion(
        autofilled_names=autofilled_names,
        event_category=data["category"],
        **base_entry_version.__dict__,
    )
