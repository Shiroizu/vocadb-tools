from vdbpy.parsers.shared import (
    parse_artist_participation,
    parse_base_entry_version,
    parse_event_participations,
    parse_pvs,
)
from vdbpy.types.entry_versions import (
    AlbumParticipation,
    Lyrics,
    SongVersion,
)
from vdbpy.utils.date import parse_date


def parse_song_version(data: dict) -> SongVersion:
    data, base_entry_version = parse_base_entry_version(data)

    def parse_album_participation(data) -> list[AlbumParticipation]:
        if "albums" not in data or not data["albums"]:
            return []
        album_participations = []
        for album_participation in data["albums"]:
            album_participations.append(
                AlbumParticipation(
                    disc_number=album_participation["discNumber"],
                    track_number=album_participation["trackNumber"],
                    album_id=album_participation["id"],
                    name_hint=album_participation["nameHint"],
                )
            )
        return album_participations

    def parse_lyrics(data) -> list[Lyrics]:
        if "lyrics" not in data or not data["lyrics"]:
            return []
        lyrics = []
        for lyric in data["lyrics"]:
            lyrics.append(
                Lyrics(
                    language_codes=lyric.get("cultureCodes", []),
                    lyrics_id=lyric["id"],
                    source=lyric.get("source", ""),
                    translation_type=lyric["translationType"],
                    url=lyric.get("url", ""),
                    value=lyric.get("value", ""),
                )
            )
        return lyrics

    return SongVersion(
        albums=parse_album_participation(data),
        artists=parse_artist_participation(data),
        length=data.get("lengthSeconds", 0),
        lyrics=parse_lyrics(data),
        original_version_id=data["originalVersion"]["id"]
        if "originalVersion" in data
        else 0,
        publish_date=parse_date(data["publishDate"]) if "publishDate" in data else None,
        pvs=parse_pvs(data),
        release_events=parse_event_participations(data),
        song_type=data["songType"],
        **base_entry_version.__dict__,
    )
