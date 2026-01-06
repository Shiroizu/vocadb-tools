from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.series import ReleaseEventSeriesVersion


def parse_release_event_series_version(
    data: dict[Any, Any],
) -> ReleaseEventSeriesVersion:
    version_data = data["versions"]["firstData"]
    return ReleaseEventSeriesVersion(
        event_category=version_data["category"],
        **parse_base_entry_version(data).__dict__,
    )
