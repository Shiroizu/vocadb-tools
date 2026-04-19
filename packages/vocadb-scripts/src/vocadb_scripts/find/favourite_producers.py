"""Generate a table of user's favourite producers."""

# TODO ignore non-music-producers

import argparse
from datetime import UTC, datetime, timedelta
from typing import Any

import tabulate as tabulate_module
from tabulate import tabulate
from vdbpy.api.artists import (
    get_artist_by_id_7d,
    get_artist_details_by_id_7d,
    get_cached_followed_artists_by_user_id,
)
from vdbpy.api.songs import (
    get_cached_rated_songs_with_ratings,
    get_most_rated_song_by_artist_id_7d,
    get_most_recent_song_by_artist_id_1d,
    get_songs_with_total_count,
)
from vdbpy.api.users import get_username_by_id
from vdbpy.config import SONG_API_URL, WEBSITE
from vdbpy.parsers.songs import parse_song
from vdbpy.types.songs import SongEntry, SongSearchParams
from vdbpy.utils.cache import get_vdbpy_cache_dir
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json

tabulate_module.WIDE_CHARS_MODE = True
logger = get_logger()

def get_youtube_link(artist_entry: dict[Any, Any]) -> str:
    if "webLinks" not in artist_entry:
        logger.warning("Artist entry does not include any external links!")
        return ""
    for link in artist_entry["webLinks"]:
        if (
            link["category"] == "Official"
            and not link["disabled"]
            and link["url"].startswith("https://www.youtube.com/")
        ):
            return link["url"]
    return ""


def get_days_since_song_publish_date(song_entry, today: datetime) -> int:
    if not song_entry.publish_date:
        logger.warning(f"Song {song_entry.id} does not include a publish date!")
        return -1

    if song_entry.publish_date > today:
        logger.warning(f"Song {song_entry.id} has a publish date in the future!")
        return -1

    return (today - song_entry.publish_date).days


def build_top_favourite_producers(
    rated_songs: list[dict[str, Any]],
    limit: int = 50,
) -> list[tuple[int, str, float]]:
    unique_artists = build_producer_score_map(rated_songs)
    rows: list[tuple[int, str, float]] = []
    for aid, v in unique_artists.items():
        score = float(v[1] * 3 + v[2] * 2)
        if score <= 0:
            continue
        rows.append((aid, str(v[0]), score))
    rows.sort(key=lambda x: x[2], reverse=True)
    return rows[:limit]


def build_producer_score_map(rated_songs: list[dict[str, Any]]) -> dict[int, list[Any]]:
    """Return artist_id -> [name, favs, likes] for producers from rated songs."""
    unique_artists: dict[int, list[Any]] = {}
    for song in rated_songs:
        placeholder = ""
        rating = song["rating"]
        try:
            for artist in song["song"]["artists"]:
                if "Producer" in artist["categories"]:
                    placeholder = artist["name"]
                    artist_id = artist["artist"]["id"]
                    if artist_id in unique_artists:
                        if rating == "Favorite":
                            unique_artists[artist_id][1] += 1
                        elif rating == "Like":
                            unique_artists[artist_id][2] += 1
                    elif rating == "Favorite":
                        unique_artists[artist_id] = [artist["artist"]["name"], 1, 0]
                    elif rating == "Like":
                        unique_artists[artist_id] = [artist["artist"]["name"], 0, 1]
        except KeyError:
            logger.debug(f"Custom artist '{placeholder}' on S/{song['song']['id']}")
            continue
    return unique_artists


def find_favourite_producers_by_user_id(user_id: int, max_results: int):
    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite producers for user '{username}' ({user_id})")

    rated_songs = get_cached_rated_songs_with_ratings(user_id)
    unique_artists = build_producer_score_map(rated_songs)

    logger.info(f"Found {len(unique_artists)} unique artists...")

    unique_artists_with_score = []
    for ar_id, (name, favs, likes) in unique_artists.items():
        score = favs * 3 + likes * 2
        unique_artists_with_score.append([name, favs, likes, score, ar_id])

    unique_artists_with_score.sort(key=lambda x: x[3], reverse=True)

    logger.info("Fetching followed artists...")
    followed_artists = get_cached_followed_artists_by_user_id(user_id)
    followed_artists_ids = [int(artist["id"]) for artist in followed_artists]

    headers = [
        "Score",
        "Artist",
        "Favs",
        "Likes",
        "Favs/Likes",
        "Rated %",
        "Score/Followers",
        "Following",
        "Entry",
        "Youtube",
        "Most rated song",
        "Days since last song",
    ]
    table_to_print = []
    best_ratio = 0.0
    best_gem: tuple[str, int, int, str] | None = None
    today = datetime.now(tz=UTC)
    for counter, ar in enumerate(unique_artists_with_score[:max_results], start=1):
        logger.info(f"Generating row for artist {counter}/{max_results}: {ar}...")
        name, favs, likes, score, ar_id = ar
        artist_entry = get_artist_by_id_7d(ar_id, fields=["webLinks"])
        details = get_artist_details_by_id_7d(ar_id)
        shared_stats = details.get("sharedStats", {})
        songcount_by_artist = shared_stats.get("songCount", 0)
        rated_songs_percentage = (
            round(((favs + likes) / songcount_by_artist * 100), 1)
            if songcount_by_artist
            else 0
        )
        most_rated_song = get_most_rated_song_by_artist_id_7d(ar_id)
        most_recent_song = get_most_recent_song_by_artist_id_1d(ar_id)
        entry_url = f"{WEBSITE}/Ar/{ar_id}"
        followers = shared_stats.get("followerCount", 0)
        ratio = round(score / followers, 3) if followers else 0.0
        line_to_print = (
            score,
            name,
            favs,
            likes,
            round(favs / likes, 1) if likes else 0,
            rated_songs_percentage,
            ratio,
            ar_id in followed_artists_ids,
            entry_url,
            get_youtube_link(artist_entry),
            f"{WEBSITE}/S/{most_rated_song.id}",
            get_days_since_song_publish_date(most_recent_song, today),
        )
        table_to_print.append(line_to_print)
        if ratio > best_ratio:
            best_ratio = ratio
            best_gem = (name, score, followers, entry_url)

    return headers, table_to_print, best_gem


def _get_rated_song_ids_for_artist(
    rated_songs: list[dict[str, Any]],
    artist_id: int,
) -> tuple[set[int], int]:
    """Return (rated_song_ids, rated_with_pvs_count) for a specific artist."""
    rated_ids: set[int] = set()
    rated_with_pvs = 0
    for rs in rated_songs:
        for artist in rs["song"].get("artists", []):
            try:
                if artist["artist"]["id"] == artist_id:
                    song_id = rs["song"]["id"]
                    rated_ids.add(song_id)
                    pv_services = rs["song"].get("pvServices", "Nothing")
                    if pv_services and pv_services != "Nothing":
                        rated_with_pvs += 1
                    break
            except (KeyError, TypeError):
                continue
    return rated_ids, rated_with_pvs


def _pct(part: int, whole: int) -> str:
    return f"{round(part / whole * 100, 1)}%" if whole else "0%"


def _score_emoji(score: int) -> str:
    if score > 100:
        return "💯"
    if score >= 50:
        return "⭐"
    if score >= 10:
        return "⬆️"
    return ""


def _has_producer_role(song: SongEntry, artist_id: int) -> bool:
    if song.artists == "Unknown":
        return False
    for ap in song.artists:
        if isinstance(ap.entry, str):
            continue
        if ap.entry.artist_id == artist_id and "Producer" in ap.categories:
            return True
    return False


def get_producer_deep_dive(user_id: int, artist_id: int) -> str:
    """Detailed stats for a specific producer relative to a user's library."""
    artist_entry = get_artist_by_id_7d(artist_id)
    artist_name = artist_entry.get("name", f"Artist {artist_id}")
    if artist_entry.get("artistType") != "Producer":
        raise ValueError(
            f"{artist_name} (Ar/{artist_id}) is not a Producer."
        )

    # Total song count
    _, total_songs = get_songs_with_total_count(
        song_search_params=SongSearchParams(artist_ids={artist_id}, max_results=1),
    )

    # Songs with PVs count
    _, total_with_pvs = get_songs_with_total_count(
        song_search_params=SongSearchParams(
            artist_ids={artist_id}, only_with_pvs=True, max_results=1,
        ),
    )

    # Date range (newest and oldest publish dates)
    date_range = ""
    if total_songs > 0:
        newest, _ = get_songs_with_total_count(
            song_search_params=SongSearchParams(
                artist_ids={artist_id}, sort="PublishDate", max_results=1,
            ),
        )
        # fetch_json_items_with_total_count always resets start=0, so use fetch_json
        # directly to get the last song in the sorted list (= oldest)
        oldest_result = fetch_json(
            SONG_API_URL,
            params={
                "artistId[]": str(artist_id),
                "sort": "PublishDate",
                "start": total_songs - 1,
                "maxResults": 1,
            },
        )
        oldest = [parse_song(s) for s in oldest_result.get("items", [])]
        if oldest and newest and oldest[0].publish_date and newest[0].publish_date:
            start = oldest[0].publish_date.strftime("%Y-%m")
            end = newest[0].publish_date.strftime("%Y-%m")
            date_range = f" ({start} - {end})"

    # User's rated songs for this artist
    rated_songs = get_cached_rated_songs_with_ratings(user_id)
    rated_ids, rated_with_pvs = _get_rated_song_ids_for_artist(rated_songs, artist_id)
    rated_count = len(rated_ids)

    # Top 5 unrated by rating score (PVs only, producer role only)
    top_songs, _ = get_songs_with_total_count(
        fields={"artists"},
        song_search_params=SongSearchParams(
            artist_ids={artist_id}, only_with_pvs=True,
            sort="RatingScore", max_results=100,
        ),
    )
    top_unrated = [
        s for s in top_songs
        if s.id not in rated_ids
        and _has_producer_role(s, artist_id)
        and s.song_type != "Instrumental"
    ][:5]

    # 5 most recent unrated (PVs only, producer role only)
    recent_songs, _ = get_songs_with_total_count(
        fields={"artists"},
        song_search_params=SongSearchParams(
            artist_ids={artist_id}, only_with_pvs=True,
            sort="PublishDate", max_results=100,
        ),
    )
    recent_unrated = [
        s for s in recent_songs
        if s.id not in rated_ids
        and _has_producer_role(s, artist_id)
        and s.song_type != "Instrumental"
    ][:5]

    # Build output
    pv_pct = _pct(total_with_pvs, total_songs)
    rated_pct = _pct(rated_count, total_songs)
    rated_pv_pct = _pct(rated_with_pvs, total_with_pvs)
    lines = [
        f"**{artist_name}** ({WEBSITE}/Ar/{artist_id})",
        "",
        f"Songs: {total_songs}{date_range}",
        f"With PVs: {total_with_pvs} / {total_songs} ({pv_pct})",
        f"Rated: {rated_count} / {total_songs} ({rated_pct})",
        f"Rated (PVs only): {rated_with_pvs} / {total_with_pvs}"
        f" ({rated_pv_pct})",
    ]

    if top_unrated:
        lines.append("")
        lines.append("**Top unrated songs** (by rating score, PVs only):")
        for i, s in enumerate(top_unrated, 1):
            emoji = _score_emoji(s.rating_score)
            score_str = f"{emoji} {s.rating_score}" if emoji else str(s.rating_score)
            lines.append(
                f"{i}. {s.default_name} {score_str} <{WEBSITE}/S/{s.id}>"
            )

    if recent_unrated:
        lines.append("")
        lines.append("**Most recent unrated** (PVs only):")
        for i, s in enumerate(recent_unrated, 1):
            date_str = s.publish_date.strftime("%Y-%m-%d") if s.publish_date else "?"
            lines.append(
                f"{i}. {s.default_name} [{date_str}] <{WEBSITE}/S/{s.id}>"
            )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "user_id",
        type=int,
        help="VocaDB user id",
    )
    parser.add_argument(
        "artist_id",
        nargs="?",
        type=int,
        help="VocaDB artist id (optional - shows deep dive for specific producer)",
    )
    parser.add_argument(
        "--max_results",
        type=int,
        default=20,
        help="Maximum number of results to show",
    )

    return parser.parse_args()


def main(user_id: int, max_results: int = 20, artist_id: int | None = None) -> str:
    if artist_id:
        return get_producer_deep_dive(user_id, artist_id)

    output_path = get_vdbpy_cache_dir() / "favourite-producers" / f"{user_id}.csv"
    if output_path.exists():
        age = datetime.now(tz=UTC) - datetime.fromtimestamp(
            output_path.stat().st_mtime, tz=UTC
        )
        if age < timedelta(days=7):
            logger.info(
                f"Cache hit: '{output_path}' is {age.days}d old, skipping rebuild"
            )
            return output_path.read_text(encoding="utf-8")
    headers, producer_table, hidden_gem = find_favourite_producers_by_user_id(
        user_id, max_results
    )
    table = tabulate(
        producer_table, headers=headers, tablefmt="github", numalign="right"
    )
    if hidden_gem:
        name, score, followers, entry_url = hidden_gem
        table += (
            f"\n\nHidden gem: {name}"
            f" (score {score}, {followers} followers, {entry_url})"
        )
    save_file(output_path, table)
    logger.info(f"\nTable saved to '{output_path}'")
    return table


if __name__ == "__main__":
    args = parse_args()
    logger = get_logger("find_favourite_producers")
    result = main(args.user_id, args.max_results, args.artist_id)
    logger.info(f"\n{result}")
