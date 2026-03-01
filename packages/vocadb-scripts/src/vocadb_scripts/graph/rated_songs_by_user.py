"""Rated songs by publish month graph."""

import sys

from vdbpy.api.songs import OptionalSongFieldName, SongSearchParams, get_songs
from vdbpy.utils.logger import get_logger

from scripts.graph.graph_utils import build_figure

logger = get_logger()

_FIELDS: set[OptionalSongFieldName] = {
    "albums",
    "artists",
    "pvs",
    "releaseEvent",
    "tags",
    "webLinks",
    "cultureCodes",
}


def _collect(user_id: int, username: str) -> list[tuple[str, int]]:
    logger.info(f"Generating rated songs graph for '{username}' ({user_id})")
    rated_songs = get_songs(
        fields=_FIELDS,
        song_search_params=SongSearchParams(user_collection_id=user_id),
    )
    by_publish: dict[str, int] = {}
    for song in rated_songs:
        if song.publish_date:
            month = str(song.publish_date)[:7]
            by_publish[month] = by_publish.get(month, 0) + 1
        else:
            logger.info(f"Song S/{song.id} has no publish date.")
    return sorted(by_publish.items())


def _figure(user_id: int, username: str):
    data = _collect(user_id, username)
    return build_figure(
        data,
        f"{username}'s rated songs by publish month",
        "Songs",
        "Songs",
    )


def get_rated_songs_png(user_id: int, username: str) -> bytes:
    """Return PNG of rated songs grouped by publish month for the given user."""
    return _figure(user_id, username).to_image(format="png")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(f"Usage: {sys.argv[0]} <user_id> <username>")
    _figure(int(sys.argv[1]), sys.argv[2]).show()
