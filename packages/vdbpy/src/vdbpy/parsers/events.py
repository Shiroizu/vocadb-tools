from typing import Any

from vdbpy.parsers.shared import parse_base_entry_version
from vdbpy.types.entry_versions import (
    EventArtistParticipation,
    EventSeriesRelation,
    ReleaseEventVersion,
    SonglistRelation,
    VenueRelation,
)
from vdbpy.utils.date import parse_date


def parse_release_event_version(data: dict[Any, Any]) -> ReleaseEventVersion:
    data, base_entry_version = parse_base_entry_version(data)
    autofilled_names = (
        data["translatedName"].values()
        if "names" not in data and "translatedName" in data
        else None
    )

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

    def parse_event_artists(data: dict[Any, Any]) -> list[EventArtistParticipation]:
        if "artists" not in data or not data["artists"]:
            return []
        return [
            EventArtistParticipation(
                artist_id=event_artist["id"],
                name_hint=event_artist["nameHint"],
                roles=event_artist["roles"].split(", "),
            )
            for event_artist in data["artists"]
        ]

    return ReleaseEventVersion(
        autofilled_names=autofilled_names,
        artists=parse_event_artists(data),
        custom_venue_name=data.get("venueName", ""),
        event_category=data["category"],
        series_number=data["seriesNumber"],
        series=parse_event_series_relation(data["series"])
        if "series" in data
        else None,
        songlist=parse_songlist_relation(data["songList"])
        if "songlist" in data
        else None,
        start_date=parse_date(data["date"]) if "date" in data else None,
        venue=parse_venue_relation(data["venue"]) if "venue" in data else None,
        **base_entry_version.__dict__,
    )
