from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from typing import Any

from vdbpy.api.albums import get_albums_with_total_count
from vdbpy.api.artists import get_artists_with_total_count
from vdbpy.api.entries import get_entry_link
from vdbpy.api.events import get_events_with_total_count
from vdbpy.api.series import get_many_series_with_total_count
from vdbpy.api.songlists import get_featured_songlists_with_total_count
from vdbpy.api.songs import get_songs_with_total_count
from vdbpy.api.tags import get_tags_with_total_count
from vdbpy.api.users import get_users_with_total_count
from vdbpy.api.venues import get_venues_with_total_count
from vdbpy.types.shared import EntryType


def search_entry(name: str, entry_type: EntryType, max_results: int = 3) -> str:
    search_functions: dict[
        EntryType, tuple[Callable[..., tuple[list[Any], int]], str]
    ] = {
        "Song": (get_songs_with_total_count, "RatingScore"),
        "Album": (get_albums_with_total_count, "CollectionCount"),
        "Artist": (get_artists_with_total_count, "FollowerCount"),
        "Tag": (get_tags_with_total_count, "UsageCount"),
        "SongList": (get_featured_songlists_with_total_count, "None"),
        "Venue": (get_venues_with_total_count, "None"),
        "ReleaseEvent": (get_events_with_total_count, "None"),
        "ReleaseEventSeries": (get_many_series_with_total_count, "None"),
        "User": (get_users_with_total_count, "RegisterDate"),
    }

    params = {
        "nameMatchMode": "Exact",
        "getTotalCount": True,
        "query": name,
    }
    search_function, sort_rule = search_functions[entry_type]
    params["sort"] = sort_rule
    results, total_count = search_function(params, max_results=max_results)
    if not results or total_count > 1:
        params["nameMatchMode"] = "Auto"
        results, total_count = search_function(params, max_results=max_results)
    if not results:
        return f"No results found for '{name}'"

    links = [get_entry_link(entry_type, entry["id"]) for entry in results[:max_results]]

    if len(links) == 1:
        return links[0]

    bullet_point_links = [f"- {link}" for link in links]
    if total_count > max_results:
        bullet_point_links.append("- ...")

    return f"Found {total_count} entries for '{name}':\n{'\n'.join(bullet_point_links)}"
