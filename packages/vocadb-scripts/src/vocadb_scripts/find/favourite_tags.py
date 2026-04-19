"""Generate a table of user's favourite tags, grouped by category."""

import argparse
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

import tabulate as tabulate_module
from tabulate import tabulate
from vdbpy.api.songs import get_cached_rated_songs_with_ratings
from vdbpy.api.tags import get_tag_details_by_id_7d
from vdbpy.api.users import get_username_by_id
from vdbpy.config import WEBSITE
from vdbpy.utils.cache import get_vdbpy_cache_dir
from vdbpy.utils.dump import build_tag_direct_parent_map, build_tag_info_map
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

tabulate_module.WIDE_CHARS_MODE = True
logger = get_logger()

GENRE_LIMIT = 20
OTHER_LIMIT = 2


def build_top_favourite_genres(
    rated_songs: list[dict[str, Any]],
    tag_info: dict[int, tuple[str, str]],
    limit: int = 50,
) -> list[tuple[int, str, float]]:
    """Genre tags only, raw fav/like score per tag (no parent propagation).

    Same scoring as the favourite-tags table: ``favs * 3 + likes * 2``. Sorted
    descending for use by ``recommend_advanced`` (weighted picks from top ``limit``).
    """
    tag_map = build_tag_score_map(rated_songs)
    rows: list[tuple[int, str, float]] = []
    for tid, v in tag_map.items():
        if tag_info.get(tid, ("", ""))[1] != "Genres":
            continue
        raw = float(v[2] * 3 + v[3] * 2)
        if raw <= 0:
            continue
        rows.append((tid, str(v[0]), raw))
    rows.sort(key=lambda x: x[2], reverse=True)
    return rows[:limit]


def build_tag_score_map(rated_songs: list[dict[str, Any]]) -> dict[int, list[Any]]:
    """Return tag_id -> [name, categoryName, favs, likes] from rated songs."""
    unique_tags: dict[int, list[Any]] = {}
    for song in rated_songs:
        rating = song["rating"]
        for tag_entry in song["song"].get("tags", []):
            tag = tag_entry["tag"]
            tag_id = tag["id"]
            if tag_id in unique_tags:
                if rating == "Favorite":
                    unique_tags[tag_id][2] += 1
                elif rating == "Like":
                    unique_tags[tag_id][3] += 1
            elif rating == "Favorite":
                unique_tags[tag_id] = [tag["name"], tag["categoryName"], 1, 0]
            elif rating == "Like":
                unique_tags[tag_id] = [tag["name"], tag["categoryName"], 0, 1]
    return unique_tags


def find_favourite_tags_by_user_id(user_id: int) -> str:
    username = get_username_by_id(user_id)
    logger.info(f"Searching favourite tags for user '{username}' ({user_id})")

    rated_songs = get_cached_rated_songs_with_ratings(user_id)
    unique_tags = build_tag_score_map(rated_songs)

    logger.info(f"Found {len(unique_tags)} unique tags, propagating to parent tags...")
    direct_parent_map = build_tag_direct_parent_map()
    tag_info_map = build_tag_info_map()

    # Propagate child scores to parent tags (one level)
    for child_id in list(unique_tags):
        parent_id = direct_parent_map.get(child_id)
        if parent_id is None:
            continue
        child_favs = unique_tags[child_id][2]
        child_likes = unique_tags[child_id][3]
        if parent_id in unique_tags:
            unique_tags[parent_id][2] += child_favs
            unique_tags[parent_id][3] += child_likes
        elif parent_id in tag_info_map:
            parent_name, parent_category = tag_info_map[parent_id]
            unique_tags[parent_id] = [
                parent_name,
                parent_category,
                child_favs,
                child_likes,
            ]

    # Group by category, sorted by score descending
    by_category: dict[str, list[tuple[int, int, str, int, int]]] = defaultdict(list)
    for tag_id, (name, category, favs, likes) in unique_tags.items():
        score = favs * 3 + likes * 2
        by_category[category].append((score, tag_id, name, favs, likes))

    for entries in by_category.values():
        entries.sort(key=lambda x: x[0], reverse=True)

    # Genres first, then remaining categories alphabetically
    categories = sorted(by_category.keys(), key=lambda c: (c != "Genres", c))

    output_parts = []
    best_ratio = 0.0
    best_gem: tuple[str, int, int, str] | None = None
    for category in categories:
        limit = GENRE_LIMIT if category == "Genres" else OTHER_LIMIT
        rows: list[tuple[int, str, int, int, float, str]] = []
        for e in by_category[category][:limit]:
            score, tag_id, name, favs, likes = e
            entry_url = f"{WEBSITE}/T/{tag_id}"
            details = get_tag_details_by_id_7d(tag_id)
            followers = details.get("stats", {}).get("followerCount", 0)
            ratio = round(score / followers, 3) if followers else 0.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_gem = (name, score, followers, entry_url)
            rows.append((score, name, favs, likes, ratio, entry_url))
        section = tabulate(
            rows,
            headers=["Score", "Tag", "Favs", "Likes", "Score/Followers", "Entry"],
            tablefmt="github",
            numalign="right",
        )
        output_parts.append(f"## {category}\n\n{section}")

    result = "\n\n".join(output_parts)
    if best_gem:
        name, score, followers, entry_url = best_gem
        result += (
            f"\n\nHidden gem: {name} "
            f"(score {score}, {followers} followers, {entry_url})"
        )
    return result


def main(user_id: int) -> str:
    output_path = get_vdbpy_cache_dir() / "favourite-tags" / f"{user_id}.txt"
    if output_path.exists():
        age = datetime.now(tz=UTC) - datetime.fromtimestamp(
            output_path.stat().st_mtime, tz=UTC
        )
        if age < timedelta(days=7):
            logger.info(
                f"Cache hit: '{output_path}' is {age.days}d old, skipping rebuild"
            )
            return output_path.read_text(encoding="utf-8")
    result = find_favourite_tags_by_user_id(user_id)
    save_file(output_path, result)
    logger.info(f"\nOutput saved to '{output_path}'")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id", type=int, help="VocaDB user id")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger = get_logger("find_favourite_tags")
    result = main(args.user_id)
    logger.info(f"\n{result}")
