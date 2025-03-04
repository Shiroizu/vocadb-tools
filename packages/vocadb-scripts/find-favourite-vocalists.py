"""Print user's favourite (base) vocalists based on rated songs.

find-favourite-vocalists.py 329
Number of vocalists to print (default=10): 10
Group by base voicebank? (True/False): t

  Favs    Likes  Vocalist    Entry
------  -------  ----------  ----------------------------
  1584     3300  初音ミク    https://vocadb.net/Ar/1
   204      587  GUMI        https://vocadb.net/Ar/3
   195      536  鏡音リン    https://vocadb.net/Ar/14
    95      308  IA          https://vocadb.net/Ar/504
   106      283  巡音ルカ    https://vocadb.net/Ar/2
    80      255  鏡音レン    https://vocadb.net/Ar/15
    99      195  結月ゆかり  https://vocadb.net/Ar/134288
    55      215  v flower    https://vocadb.net/Ar/21165
    60      203  可不        https://vocadb.net/Ar/83928
    69      183  重音テト    https://vocadb.net/Ar/140308

Table saved to 'output/favourite-vocalists-329.txt'
"""

import os
import sys

from tabulate import tabulate

from api.artists import get_base_voicebank
from api.users import get_rated_songs
from utils.console import get_boolean, get_parameter
from utils.files import save_file

user_id = int(get_parameter("VocaDB user id: ", sys.argv, integer=True))
output_length = int(
    get_parameter("Number of vocalists to print: ", integer=True, default="10")
)
base_vbs_only = get_boolean("Group by base voicebank?")

output_directory = "output"
filename = f"favourite-vocalists-{user_id}.txt"
save_location = os.path.join(output_directory, filename)

unique_vocalists = {}
extra_params = {"fields": "Artists"}
rated_songs = get_rated_songs(int(user_id), extra_params)

for song in rated_songs:
    placeholder = ""
    rating = song["rating"]
    try:
        for artist in song["song"]["artists"]:
            if "Vocalist" in artist["categories"]:
                placeholder = artist["name"]
                artist_id = artist["artist"]["id"]
                if artist_id in unique_vocalists:
                    if rating == "Favorite":
                        unique_vocalists[artist_id][1] += 1
                    elif rating == "Like":
                        unique_vocalists[artist_id][2] += 1
                elif rating == "Favorite":
                    unique_vocalists[artist_id] = [artist["artist"]["name"], 1, 0]
                elif rating == "Like":
                    unique_vocalists[artist_id] = [artist["artist"]["name"], 0, 1]
    except KeyError:
        # print(f"Custom artist '{placeholder}' on S/{song['song']['id']}")
        continue

unique_vocalists_with_score = []

for ar_id in unique_vocalists:
    name, favs, likes = [
        unique_vocalists[ar_id][0],
        unique_vocalists[ar_id][1],
        unique_vocalists[ar_id][2],
    ]
    score = favs * 3 + likes * 2
    unique_vocalists_with_score.append([name, favs, likes, score, ar_id])


if base_vbs_only:
    score_by_base_vb = {}
    # name: [favs, likes, score, id]
    for counter, vb in enumerate(unique_vocalists_with_score):
        vb_name, favs, likes, score, vb_id = vb
        base_vb = get_base_voicebank(vb_id)
        base_name = base_vb["name"]
        if vb_name != base_name:
            print(
                f"{counter+1}/{len(unique_vocalists_with_score)} Base VB for '{vb_name}' is '{base_name}'"
            )
        if base_name in score_by_base_vb:
            score_by_base_vb[base_name][0] += favs
            score_by_base_vb[base_name][1] += likes
            score_by_base_vb[base_name][2] += score
        else:
            score_by_base_vb[base_name] = [favs, likes, score, base_vb["id"]]

    print(score_by_base_vb)
    unique_vocalists_with_score = [
        [name, *stats] for name, stats in score_by_base_vb.items()
    ]

print(unique_vocalists_with_score)
unique_vocalists_with_score.sort(key=lambda x: x[3], reverse=True)


table_to_print = []
for ar in unique_vocalists_with_score[:output_length]:
    name, favs, likes, score, ar_id = ar
    if name.lower().endswith(" (unknown)"):
        name = name[:-10]
    line_to_print = (favs, likes, name, f"https://vocadb.net/Ar/{ar_id}")
    table_to_print.append(line_to_print)

table = tabulate(table_to_print, headers=["Favs", "Likes", "Vocalist", "Entry"])
print(f"\n{table}")

save_file(save_location, table)
print(f"\nTable saved to '{save_location}'")
