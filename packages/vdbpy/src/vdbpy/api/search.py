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

# TODO save results by copypasting browser url


def search_entries(
    name: str,
    entry_type: EntryType,
    max_results: int = 3,
    extra_params: dict[Any, Any] | None = None,
) -> tuple[list[Any], int]:
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
    if extra_params:
        for field, value in extra_params.items():
            if field not in params:
                params[field] = value
    search_function, sort_rule = search_functions[entry_type]
    params["sort"] = sort_rule
    results, total_count = search_function(params, max_results=max_results)
    if not results or total_count > 1:
        params["nameMatchMode"] = "Auto"
        results, total_count = search_function(params, max_results=max_results)
    if not results:
        return [], 0
    return results, total_count


def search_entry_links(name: str, entry_type: EntryType, max_results: int = 3) -> str:
    entries, total_count = search_entries(name, entry_type, max_results)
    if not entries:
        return f"No results found for '{name}'"

    entry_ids = [int(entry["id"]) for entry in entries]
    links = [
        get_entry_link(entry_type, entry_id) for entry_id in entry_ids[:max_results]
    ]

    if len(links) == 1:
        return links[0]

    bullet_point_links = [f"- {link}" for link in links]
    if total_count > max_results:
        bullet_point_links.append("- ...")

    return f"Found {total_count} entries for '{name}':\n{'\n'.join(bullet_point_links)}"
