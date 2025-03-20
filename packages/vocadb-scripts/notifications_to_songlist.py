import datetime
import sys
import time

import requests

from api.songlists import create_songlists
from api.users import delete_notifications
from utils.console import get_parameter

user_id = int(get_parameter("VocaDB user id: ", sys.argv, integer=True)) # TODO arg_parser

CREDENTIALS_FILE = "credentials.env" # TODO get_credentials
SEEN_SONG_IDS_FILE = "data/seen song ids.txt" # TODO validate path
NOTIF_LOG_FILE = "output/notifications.txt" # TODO validate path
PAGE_SIZE = 50
MAX_NOTIFS = 400
CHECK_ONLY_UNREAD = True # TODO move script parameter
MAX_SONGLIST_LENGTH = 200 # TODO move to script parameter

def get_new_songlinks(session: requests.Session) -> list[str]:
    # TODO move to api.songlists
    notification_ids: list[str] = []
    notification_messages: list[str] = []
    new_song_ids: list[str] = []
    page = 1

    while True:
        params = {
            "inbox": "Notifications",
            "unread": CHECK_ONLY_UNREAD,
            "maxResults": PAGE_SIZE,
            "start": (page - 1) * PAGE_SIZE,
        }

        if CHECK_ONLY_UNREAD:
            params["start"] = 0

        if page * PAGE_SIZE > MAX_NOTIFS:
            print(f"Max notif count reached {MAX_NOTIFS}")
            break

        r = session.get(f"https://vocadb.net/api/users/{user_id}/messages", params=params)
        print(f"Fetched {r.url}")
        notifs = r.json()["items"]

        if not notifs:
            break

        print(f"Found {len(notifs)} notifications")
        notification_ids.extend([n["id"] for n in notifs])

        for item in notifs:
            notif_body = session.get(
                f"https://vocadb.net/api/users/messages/{item['id']}"
            ).json()["body"]
            notification_messages.append(notif_body)
            if "song" in item["subject"]:
                song_id = notif_body.split("/S/")[-1].split(")',")[0].split("?")[0]
                print(f"\t{item['subject']} https://vocadb.net/S/{song_id}")

                # Skip duplicate notifs
                if song_id in new_song_ids:
                    print("Duplicate notification detected!")
                    continue

                new_song_ids.append(song_id)

            elif "album" in item["subject"]:
                album_id = notif_body.split("/Al/")[-1].split(")',")[0]
                print(f"\t{item['subject']} https://vocadb.net/Al/{album_id}")

            elif "A new artist" in item["subject"]:
                # A new artist, '[sakkyoku645](https://vocadb.net/Ar/48199)', tagged with funk was just added.
                start, end = item["subject"].split("', tagged with ")
                artist_name, artist_url = start.split("](")
                artist_name = artist_name.split("[")[1]
                artist_url = artist_url.split(")")[0]
                tag_name = end.split(" was just")[0]
                print(f"\tArtist tagged with '{tag_name}': {artist_name} {artist_url}")

            else:
                print(f"\t{notif_body}")

        page += 1
        time.sleep(1)

    if notification_ids:
        delete_notifications(session, user_id, notification_ids)
        with open(NOTIF_LOG_FILE, "a", encoding="utf8") as f:
            for notif_message in notification_messages:
                f.write(f"{notif_message}\n")

    print(f"Found {len(new_song_ids)} new songs to check")

    return new_song_ids


def remove_seen_songs(new_song_ids: list[str]):
    # TODO use shared list functions
    with open(SEEN_SONG_IDS_FILE) as f:
        seen_song_ids = list(set(f.read().splitlines()))

    unseen_song_ids = []
    removed = 0

    for song_id in set(new_song_ids):
        if song_id in seen_song_ids:
            removed += 1
        else:
            unseen_song_ids.append(song_id)

    print(f"{removed}/{len(new_song_ids)} ids filtered out")

    with open("new song ids.txt", "w") as f:
        f.write("")  # clear file

    return unseen_song_ids


if __name__ == "__main__":
    with open(CREDENTIALS_FILE) as f:
        un, pw = f.read().splitlines()
        login = {"UserName": un, "password": pw}

    with requests.Session() as session:
        print("Logging in...")
        session.post("https://vocadb.net/User/Login", data=login)
        new_songs = get_new_songlinks(session)
        unseen_songs = remove_seen_songs(new_songs)
        date = str(datetime.datetime.now())[:10]  # YYYY-MM-DD
        songlist_title = f"Songs to check {date}"
        create_songlists(session, songlist_title, unseen_songs)
        with open(SEEN_SONG_IDS_FILE, "a") as f:
            for song_id in unseen_songs:
                f.write(f"{song_id}\n")
