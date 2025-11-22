from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from pathlib import Path
from typing import Any, get_args

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
from vdbpy.config import WEBSITE
from vdbpy.types.artists import VoicebankType
from vdbpy.types.shared import EntryType
from vdbpy.utils.console import prompt_choice
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

logger = get_logger()


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


def find_vocalist_id(name: str) -> int:
    # 1) find by exact match
    #    - if 1 vocalist result, return that
    # 2) if multiple results, find unknown vb
    #    - if 1 vocalist result, return that
    # 3) prompt for id (display top 5 vocalist choices)
    #    - if prompt != 0, return that
    # 4) prompt for id (create entry manually)

    params = {"artistTypes": ",".join([vb.lower() for vb in get_args(VoicebankType)])}
    first_search, total_count = search_entries(
        name, "Artist", max_results=10, extra_params=params
    )
    if first_search:
        if len(first_search) == 1:
            vocalist_entry = first_search[0]
            if vocalist_entry["artistType"] not in get_args(VoicebankType):
                logger.warning(f"'{name}' is not a voicebank")
            else:
                vocalist_id = vocalist_entry["id"]
                logger.info(
                    f"Found {WEBSITE}/Ar/{vocalist_id} \
                        ({vocalist_entry['artistType']}): '{vocalist_entry['name']}'"
                )
                return vocalist_id
        else:
            logger.info(f"Too many results for '{name}' ({total_count})")

        second_search, total_count = search_entries(
            name + " (Unknown)", "Artist", max_results=5, extra_params=params
        )
        if len(second_search) == 1:
            vocalist_entry = second_search[0]
            if vocalist_entry["artistType"] not in get_args(VoicebankType):
                logger.warning(f"'  {name}' is not a voicebank")
            else:
                vocalist_id = vocalist_entry["id"]
                logger.info(
                    f"  Found {WEBSITE}/Ar/{vocalist_id} \
                        ({vocalist_entry['artistType']}): '{vocalist_entry['name']}'"
                )
                return second_search[0]["id"]
        else:
            logger.info(
                f"  Incorrect amount of results for '{name} (Unknown)' ({total_count})"
            )

        choices: list[str] = [
            f"{WEBSITE}/Ar/{vocalist_entry['id']} \
                ({vocalist_entry['artistType']}): '{vocalist_entry['name']}'"
            for vocalist_entry in first_search
        ]
        chosen_entry = prompt_choice(choices, allow_skip=True)
        if chosen_entry:
            return int(chosen_entry.split()[0])
    else:
        logger.info(f"No results for '{name}'")

    return int(input("Manually created vocalist id: ").strip())


def get_vocalists_ids(
    vocalist_line: str,
    vocalist_id_mapping: dict[str, int],
    vocalist_mapping_file: Path,
    delimiter: str = ",",
) -> list[int]:
    logger.debug(f"Vocalists are '{vocalist_line}'")
    vocalist_ids: list[int] = []
    for v in vocalist_line.split(","):
        stripped_name = v.strip()
        if stripped_name in vocalist_id_mapping:
            vocalist_ids.append(vocalist_id_mapping[stripped_name])
        else:
            vocalist_id = find_vocalist_id(stripped_name)
            vocalist_ids.append(vocalist_id)
            vocalist_id_mapping[stripped_name] = vocalist_id
            save_file(
                vocalist_mapping_file,
                f"{stripped_name}{delimiter}{vocalist_id}",
                append=True,
            )
    return vocalist_ids
