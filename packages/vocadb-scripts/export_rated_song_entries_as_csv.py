import argparse

from vdbpy.api.users import get_rated_songs
from vdbpy.utils.files import save_file
from vdbpy.utils.logger import get_logger

logger = get_logger("export_rated_song_entries_as_csv")


def list_to_string_or_zero(data: list[str]) -> str:
    return LIST_DELIMITER.join(data) if data else "0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "user_id",
        type=int,
        help="VocaDB user id",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    user_id = args.user_id

    OUTPUT_FILE = f"output/rated-songs-{user_id}.csv"
    COLUMN_DELIMITER = ";"
    LIST_DELIMITER = ","

    fields = [
        "Albums",
        "Artists",
        "PVs",
        "ReleaseEvent",
        "Tags",
        "WebLinks",
        "CultureCodes",
    ]

    params = {"fields": ", ".join(fields)}
    rated_songs = get_rated_songs(user_id, params)

    simple_columns = {
        "Song id": "id",
        "Name": "defaultName",
        "Total score": "ratingScore",
        "Times favorited": "favoritedTimes",
        "Entry created": "createDate",
        "Publish date": "publishDate",
        "PV services": "pvServices",
        "Song type": "songType",
        "Entry status": "status",
    }

    headers = list(simple_columns.keys())
    headers.extend(
        [
            "Rating date",
            "Own score",
            "Tag ids",
            "Album ids",
            "Producer ids",
            "Vocalist ids",
            "Other artist ids",
            "Number of external links",
            "Languages",
        ]
    )

    save_file(OUTPUT_FILE, COLUMN_DELIMITER.join(headers))

    for song in rated_songs:
        output_line: list[str] = []
        entry = song["song"]
        for value in simple_columns.values():
            try:
                output_line.append(str(entry[value]).replace(COLUMN_DELIMITER, " "))
            except KeyError:
                logger.info(f"{value} not found for {entry['id']}")
                output_line.append("?")

        output_line.append(song["date"])  # rating date

        own_score = 3 if (song["rating"] == "Favorite") else 2
        output_line.append(str(own_score))

        tag_ids = []
        if "tags" in entry:
            tag_ids = [str(tag["tag"]["id"]) for tag in entry["tags"]]
        output_line.append(list_to_string_or_zero(tag_ids))

        album_ids = [str(album["id"]) for album in entry["albums"]]
        output_line.append(list_to_string_or_zero(album_ids))

        producer_ids = []
        vocalist_ids = []
        other_artist_ids = []

        if "artists" in entry:
            for artist in entry["artists"]:
                if "categories" in artist:
                    if artist["categories"] == "Producer":
                        producer_ids.append(str(artist["id"]))
                    elif artist["categories"] == "Vocalist":
                        vocalist_ids.append(str(artist["id"]))
                    else:
                        other_artist_ids.append(str(artist["id"]))

        output_line.append(list_to_string_or_zero(producer_ids))
        output_line.append(list_to_string_or_zero(vocalist_ids))
        output_line.append(list_to_string_or_zero(other_artist_ids))

        if "webLinks" in entry:
            output_line.append(str(len(entry["webLinks"])))
        else:
            output_line.append("0")

        output_line.append(list_to_string_or_zero(entry["cultureCodes"]))
        if len(output_line) != len(headers):
            logger.info("The column length size is mismatching with headers")
            logger.info(output_line)
            logger.info(len(output_line))
            logger.info(headers)
            logger.info(len(headers))
            _ = input("Press enter to continue")

        save_file(OUTPUT_FILE, COLUMN_DELIMITER.join(output_line), append=True)
