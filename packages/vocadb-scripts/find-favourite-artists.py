"""Print users favourite artists based on rated songs.

find-favourite-artists.py {user_id_here}
Number of artists to print: 10

Fetching rated songs for user id 26917
Found total of 190 rated songs
Fetching followed artists for user id 26917
Found total of 5 followed artists

  Favs    Likes  Artist          Entry
------  -------  --------------  -------------------------------------------
    21       18  煮ル果実        https://vocadb.net/Ar/64434
    20       11  いよわ          https://vocadb.net/Ar/65229
     8        8  NMKK            https://vocadb.net/Ar/68393
     8        6  はるまきごはん  https://vocadb.net/Ar/28208
     2        3  否め            https://vocadb.net/Ar/66067 (not following)
     4        0  ヒッキーP       https://vocadb.net/Ar/531 (not following)
     2        3  john            https://vocadb.net/Ar/72348 (not following)
     0        5  ピノキオピー    https://vocadb.net/Ar/28 (not following)
     2        0  ハチ            https://vocadb.net/Ar/49 (not following)
     2        0  柊キライ        https://vocadb.net/Ar/70641 (not following)

"""

import os
import sys

from tabulate import tabulate

from api.users import get_followed_artists, get_rated_songs
from utils.console import get_parameter
from utils.files import save_file

user_id = int(get_parameter("VocaDB user id: ", sys.argv, integer=True))
output_length = int(get_parameter("Number of artists to print: ", integer=True))
output_directory = "output"
filename = f"favourite-arists-{user_id}.txt"
save_location = os.path.join(output_directory, filename)

print("\n")
unique_artists = {}
extra_params = {"fields": "Artists"}
rated_songs = get_rated_songs(int(user_id), extra_params)

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
        # print(f"Custom artist '{placeholder}' on S/{song['song']['id']}")
        continue


unique_artists_with_score = []

for ar_id in unique_artists:
    name, favs, likes = [
        unique_artists[ar_id][0],
        unique_artists[ar_id][1],
        unique_artists[ar_id][2],
    ]
    score = favs * 3 + likes * 2
    unique_artists_with_score.append([name, favs, likes, score, ar_id])

unique_artists_with_score.sort(key=lambda x: x[3], reverse=True)

followed_artists = []
page = 1

follower_artists = get_followed_artists(user_id)

if not output_length:
    output_length = None

table_to_print = []
for ar in unique_artists_with_score[:output_length]:
    follow_msg = "(not following)"
    name, favs, likes, score, ar_id = ar
    if ar_id in followed_artists:
        follow_msg = ""
    line_to_print = (favs, likes, name, f"https://vocadb.net/Ar/{ar_id} {follow_msg}")
    table_to_print.append(line_to_print)

table = tabulate(table_to_print, headers=["Favs", "Likes", "Artist", "Entry"])
print(f"\n{table}")

save_file(save_location, table)
print(f"nTable saved to '{save_location}'")
