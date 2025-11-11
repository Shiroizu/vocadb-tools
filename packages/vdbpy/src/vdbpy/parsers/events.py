from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.events import (
    ReleaseEvent,
    ReleaseEventVersion,
    VersionEventArtistParticipation,
)
from vdbpy.types.series import EventSeriesRelation
from vdbpy.types.songlists import SonglistRelation
from vdbpy.types.venues import VenueRelation
from vdbpy.utils.date import parse_date


def parse_event_series_relation(data: dict[Any, Any]) -> EventSeriesRelation:
    return EventSeriesRelation(
        series_id=data["id"],
        name_hint=data["nameHint"],
    )


def parse_songlist_relation(data: dict[Any, Any]) -> SonglistRelation:
    return SonglistRelation(
        songlist_id=data["id"],
        name_hint=data["nameHint"],
    )


def parse_venue_relation(data: dict[Any, Any]) -> VenueRelation:
    return VenueRelation(
        venue_id=data["id"],
        name_hint=data["nameHint"],
    )


def parse_event_artists(
    data: dict[Any, Any],
) -> list[VersionEventArtistParticipation]:
    if "artists" not in data or not data["artists"]:
        return []
    return [
        VersionEventArtistParticipation(
            artist_id=event_artist["id"],
            name_hint=event_artist["nameHint"],
            roles=event_artist["roles"].split(", "),
        )
        for event_artist in data["artists"]
    ]


def parse_release_event_version(data: dict[Any, Any]) -> ReleaseEventVersion:
    version_data = data["versions"]["firstData"]
    autofilled_names = (
        version_data["translatedName"].values()
        if "names" not in version_data and "translatedName" in version_data
        else None
    )

    return ReleaseEventVersion(
        autofilled_names=autofilled_names,
        artists=parse_event_artists(version_data),
        custom_venue_name=version_data.get("venueName", ""),
        event_category=version_data["category"],
        series_number=version_data["seriesNumber"],
        series=parse_event_series_relation(version_data["series"])
        if "series" in version_data
        else None,
        songlist=parse_songlist_relation(version_data["songList"])
        if "songlist" in version_data
        else None,
        start_date=parse_date(version_data["date"]) if "date" in version_data else None,
        venue=parse_venue_relation(version_data["venue"])
        if "venue" in version_data
        else None,
        **parse_base_entry_version(data).__dict__,
    )


def parse_release_event(data: dict[Any, Any]) -> ReleaseEvent:
    return ReleaseEvent(
        category=data["category"],
        date=parse_date(data["date"]),
        event_id=data["id"],
        name=data["name"],
        series_id=data.get("seriesId", 0),
        series_number=data.get("seriesNumber", 0),
        series_suffix=data.get("seriesSuffix", ""),
        status=data["status"],
        url_slug=data["urlSlug"],
        venue_name=data.get("venueName", ""),
        version_count=data["version"],
    )
