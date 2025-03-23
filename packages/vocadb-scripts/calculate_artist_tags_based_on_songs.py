import argparse

from api.artists import get_artist
from api.songs import get_songs_by_artist

""" Example output:

Artist 'しじみ' (Ar/2595) - Most common tags:
|   entry_count |   votes | name                      | category     |   tag_id |
|---------------|---------|---------------------------|--------------|----------|
|             3 |       5 | karaoke available         | Distribution |     3113 |
|             1 |       1 | first work                | Sources      |      158 |
|             1 |       1 | electronica               | Genres       |     1580 |
|             1 |       3 | electropop                | Genres       |      124 |
|             1 |       1 | free                      | Distribution |      160 |
|             1 |       3 | MMD                       | Animation    |      275 |
|             1 |       3 | シテヤンヨ                 | Animation    |      394 |
|             1 |       1 | technopop                 | Genres       |     1698 |
|             1 |       1 | ままま式ミク               | MMD Models   |     3070 |
|             1 |       1 | MMD motion data available | Distribution |     8084 |
|             1 |       1 | sad                       | Subjective   |      384 |
|             1 |       1 | soft rock                 | Genres       |      403 |
|             1 |       1 | magic                     | Themes       |     6626 |
|             1 |       1 | blue                      | Themes       |     8909 |
|             1 |       1 | purple                    | Themes       |     8916 |

"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "artist_id",
        type=int,
        help="Artist id to check.",
    )
    parser.add_argument(
        "--only_with_pvs",
        type=bool,
        help="Only include entries with PVs?",
        default=False,
    )
    parser.add_argument(
        "--participation_status",
        type=str,
        choices=["all", "only_main", "only_collabs"],
        default="only_main",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    only_with_pvs = args.only_with_pvs
    param_mapping = {
        "all": "Everything",
        "only_main": "OnlyMainAlbums",
        "only_collabs": "OnlyCollaborations",
    }

    participation_status = param_mapping[args.participation_status]

    params = {
        "fields": "Tags",
        "onlyWithPvs": only_with_pvs,
        "artistParticipationStatus": participation_status,
    }
    args = parse_args()
    artist_id = args.artist_id
    songs_by_artist = get_songs_by_artist(artist_id, params)
    tag_counts = {}
    for song in songs_by_artist:
        """ count	1
            tag
                additionalNames	"kpop"
                categoryName	"Genres"
                id	            1700
                name	        "K-pop"
                urlSlug	        "k-pop"
        """
        for tag in song["tags"]:
            tag_data = tag["tag"]
            tag_id = tag_data["id"]
            tag_votes = tag["count"]
            if tag_id not in tag_counts:
                tag_counts[tag_id] = {
                    "entry_count": 1,
                    "votes": tag_votes,
                    "name": tag_data["name"],
                    "category": tag_data["categoryName"],
                    "tag_id": tag_id,
                }
            else:
                tag_counts[tag_id]["entry_count"] += 1
                tag_counts[tag_id]["votes"] += tag_votes

    # {158: {'votes': 1, 'name': 'first work', 'category': 'Sources', 'entry_count': 1}, 1580: {'votes': 1, 'name': 'electronica', 'category': 'Genres', 'entry_count': 1}, 3113: {'votes': 5, 'name': 'karaoke available', 'category': 'Distribution', 'entry_count': 3}, 124: {'votes': 3, 'name': 'electropop', 'category': 'Genres', 'entry_count': 1}, 160: {'votes': 1, 'name': 'free', 'category': 'Distribution', 'entry_count': 1}, 275: {'votes': 3, 'name': 'MMD', 'category': 'Animation', 'entry_count': 1}, 394: {'votes': 3, 'name': 'シテヤンヨ', 'category': 'Animation', 'entry_count': 1}, 1698: {'votes': 1, 'name': 'technopop', 'category': 'Genres', 'entry_count': 1}, 3070: {'votes': 1, 'name': 'ままま式ミク', 'category': 'MMD Models', 'entry_count': 1}, 8084: {'votes': 1, 'name': 'MMD motion data available', 'category': 'Distribution', 'entry_count': 1}, 384: {'votes': 1, 'name': 'sad', 'category': 'Subjective', 'entry_count': 1}, 403: {'votes': 1, 'name': 'soft rock', 'category': 'Genres', 'entry_count': 1}, 6626: {'votes': 1, 'name': 'magic', 'category': 'Themes', 'entry_count': 1}, 8909: {'votes': 1, 'name': 'blue', 'category': 'Themes', 'entry_count': 1}, 8916: {'votes': 1, 'name': 'purple', 'category': 'Themes', 'entry_count': 1}}

    from tabulate import tabulate

    tags_to_print = tag_counts.values()
    sorted_by_entry_count = sorted(
        tags_to_print, key=lambda x: x["entry_count"], reverse=True
    )

    artist_name = get_artist(artist_id)["name"]
    print(f"\nArtist '{artist_name}' (Ar/{artist_id}) - Most common tags:")
    print(tabulate(sorted_by_entry_count, headers="keys", tablefmt="github"))
