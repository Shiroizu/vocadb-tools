from pathlib import Path
from typing import Any, get_args

from vdbpy.api.search import search_entries
from vdbpy.config import ARTIST_API_URL, SONG_API_URL, USER_API_URL, WEBSITE
from vdbpy.types.artists import Artist, VoicebankType
from vdbpy.utils.cache import cache_with_expiration  # , cache_without_expiration
from vdbpy.utils.console import prompt_choice
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_json_items,
    fetch_json_items_with_total_count,
    fetch_total_count,
)

logger = get_logger()


def get_artists(params: dict[Any, Any] | None) -> list[Artist]:
    return fetch_json_items(ARTIST_API_URL, params=params)


def get_artists_with_total_count(
    params: dict[Any, Any] | None, max_results: int = 10**9
) -> tuple[list[Artist], int]:
    return fetch_json_items_with_total_count(
        ARTIST_API_URL, params=params, max_results=max_results
    )


def get_artists_by_tag_id(tag_id: int) -> list[Artist]:
    params = {"tagId[]": tag_id}
    return get_artists(params=params)


@cache_with_expiration(days=1)
def get_song_count_by_artist_id_1d(
    artist_id: int,
    only_main_songs: bool = False,
    extra_params: dict[Any, Any] | None = None,
) -> int:
    params = extra_params if extra_params else {}
    params["artistId[]"] = artist_id
    if only_main_songs:
        params["artistParticipationStatus"] = "OnlyMainAlbums"
    return fetch_total_count(SONG_API_URL, params)


# def get_base_voicebank_id_by_artist_id(artist_id: int, recursive: bool = True) ->
# Artist:
#     """Get base voicebank id if it exists. Return current id otherwise."""
#     params = {"fields": "baseVoiceBank"}
#     next_base_vb_id = artist_id
#     while True:
#         url = f"{ARTIST_API_URL}/{next_base_vb_id}"
#         next_base_vb = fetch_json(url, params=params)  # TODO FIX
#         if "baseVoicebank" in next_base_vb and recursive:
#             next_base_vb_id = next_base_vb["baseVoicebank"]["id"]
#             continue
#         return next_base_vb


# @cache_without_expiration()
# def get_cached_base_voicebank_by_artist_id(
#     artist_id: int, recursive: bool = True
# ) -> Artist:
#     return get_base_voicebank_id_by_artist_id(artist_id, recursive)


@cache_with_expiration(days=7)
def get_followed_artists_by_user_id_7d(
    user_id: int, extra_params: dict[Any, Any] | None = None
) -> list[Artist]:
    api_url = f"{USER_API_URL}/{user_id}/followedArtists"
    followed_artists = fetch_json_items(api_url, extra_params)
    if followed_artists:
        followed_artists = [ar["artist"] for ar in followed_artists]
    return followed_artists


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
