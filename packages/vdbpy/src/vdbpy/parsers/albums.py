from datetime import UTC, datetime
from typing import Any

from vdbpy.parsers.shared import (
    parse_artist_participation,
    parse_base_entry_version,
    parse_event_participations,
    parse_pictures,
    parse_pvs,
)
from vdbpy.types.entry_versions import AlbumTrack, AlbumVersion, Disc


def parse_album_version(data: dict[Any, Any]) -> AlbumVersion:
    data, base_entry_version = parse_base_entry_version(data)

    def parse_discs(data: dict[Any, Any]) -> list[Disc]:
        if "discs" not in data or not data["discs"]:
            return []
        return [
            Disc(
                disc_number=disc["discNumber"],
                disc_id=disc["id"],
                media_type=disc["mediaType"],
                name=disc["name"],
            )
            for disc in data["discs"]
        ]

    def parse_album_tracks(data: dict[Any, Any]) -> list[AlbumTrack]:
        if "songs" not in data or not data["songs"]:
            return []
        return [
            AlbumTrack(
                disc_number=album_track["discNumber"],
                track_number=album_track["trackNumber"],
                song_id=album_track["id"],
                name_hint=album_track["nameHint"],
            )
            for album_track in data["songs"]
        ]

    def parse_album_publish_date(
        data: dict[Any, Any],
    ) -> tuple[datetime | None, int, int, int]:
        if (
            "originalRelease" not in data
            or "releaseDate" not in data["originalRelease"]
        ):
            return None, 0, 0, 0

        data = data["originalRelease"]["releaseDate"]
        year = data.get("year", 0)
        month = data.get("month", 0)
        day = data.get("day", 0)
        publish_date = (
            datetime(year, month, day, tzinfo=UTC) if year and month and day else None
        )
        return publish_date, year, month, day

    publish_date, year, month, day = parse_album_publish_date(data)

    return AlbumVersion(
        album_type=data["discType"],
        artists=parse_artist_participation(data),
        barcodes=[code["value"] for code in data["identifiers"]]
        if "identifiers" in data
        else [],
        catalog_number=data["originalRelease"].get("catNum", "")
        if "originalRelease" in data
        else "",
        discs=parse_discs(data),
        additional_pictures=parse_pictures(data),
        publish_date=publish_date,
        publish_day=day,
        publish_month=month,
        publish_year=year,
        pvs=parse_pvs(data),  # 'publish_date': None, 'length': 0,
        release_events=parse_event_participations(data),
        songs=parse_album_tracks(data),
        **base_entry_version.__dict__,
    )
