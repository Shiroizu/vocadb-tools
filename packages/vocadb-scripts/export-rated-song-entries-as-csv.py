import os
import sys

from api.users import get_rated_songs
from utils.console import get_parameter
from utils.files import clear_file, save_file

user_id = int(get_parameter("VocaDB user id: ", sys.argv, integer=True))
output_directory = "output"
filename = f"rated-songs-{user_id}.csv"
save_location = os.path.join(output_directory, filename)

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


def list_to_string_or_zero(data: list[str]) -> str:
    return LIST_DELIMITER.join(data) if data else "0"


clear_file(save_location)
save_file(save_location, COLUMN_DELIMITER.join(headers), append=True)

for song in rated_songs:
    output_data: list[str] = []
    entry = song["song"]
    for value in simple_columns.values():
        try:
            output_data.append(str(entry[value]).replace(COLUMN_DELIMITER, " "))
        except KeyError:
            print(f"{value} not found for {entry['id']}")
            output_data.append("?")

    output_data.append(song["date"])  # rating date

    own_score = 3 if (song["rating"] == "Favorite") else 2
    output_data.append(str(own_score))

    tag_ids = []
    if "tags" in entry:
        tag_ids = [str(tag["tag"]["id"]) for tag in entry["tags"]]
    output_data.append(list_to_string_or_zero(tag_ids))

    album_ids = [str(album["id"]) for album in entry["albums"]]
    output_data.append(list_to_string_or_zero(album_ids))

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

    output_data.append(list_to_string_or_zero(producer_ids))
    output_data.append(list_to_string_or_zero(vocalist_ids))
    output_data.append(list_to_string_or_zero(other_artist_ids))

    if "webLinks" in entry:
        output_data.append(str(len(entry["webLinks"])))
    else:
        output_data.append("0")

    output_data.append(list_to_string_or_zero(entry["cultureCodes"]))
    if len(output_data) != len(headers):
        print("The column length size is mismatching with headers")
        print(output_data)
        print(len(output_data))
        print(headers)
        print(len(headers))
        _ = input("Press enter to continue")
    line = COLUMN_DELIMITER.join(output_data)
    save_file(save_location, line, append=True)

print(f"Saved '{save_location}'")
