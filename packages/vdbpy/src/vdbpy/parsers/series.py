from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.series import ReleaseEventSeriesVersion


def parse_release_event_series_version(
    data: dict[Any, Any],
) -> ReleaseEventSeriesVersion:
    version_data = data["versions"]["firstData"]
    autofilled_names = (
        version_data["translatedName"].values()
        if "names" not in version_data and "translatedName" in version_data
        else None
    )

    return ReleaseEventSeriesVersion(
        autofilled_names=autofilled_names,
        event_category=version_data["category"],
        **parse_base_entry_version(data).__dict__,
    )
