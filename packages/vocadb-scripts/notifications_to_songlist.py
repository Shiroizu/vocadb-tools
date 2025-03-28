import argparse
import datetime
import sys

import requests

from api.notifications import fetch_notifications, get_notification_body
from api.songlists import create_songlists
from api.users import delete_notifications
from utils.files import get_credentials, get_lines, save_file
from utils.logger import get_logger
from utils.network import fetch_json

logger = get_logger("notifications_to_songlist")


def is_cover_with_original_as_entry(song_id: str) -> bool:
    url = f"https://vocadb.net/api/songs/{song_id}"
    entry = fetch_json(url)
    result = (entry["songType"] == "Cover") and ("originalVersionId" in entry)
    logger.debug(f"Song {song_id} is a cover with original as entry: {result}")
    return result


def filter_notifications(
    all_notifications, session: requests.Session, skip_covers=False
) -> list[str]:
    """Returns a list of new song IDs from notifications."""
    notification_ids: list[str] = []
    notification_messages: list[str] = []
    new_song_ids: list[str] = []
    notification_messages = []

    for item in all_notifications:
        notif_body = get_notification_body(session, item["id"])
        notification_messages.append(notif_body)

        if "song" in item["subject"]:
            song_id = notif_body.split("/S/")[-1].split(")',")[0].split("?")[0]
            logger.info(f"\t{item['subject']} https://vocadb.net/S/{song_id}")

            # Skip duplicate notifs
            if song_id in new_song_ids:
                logger.debug("Duplicate notification detected!")
                continue

            if skip_covers and is_cover_with_original_as_entry(song_id):
                logger.info("\tSkipping cover song")
                continue

            new_song_ids.append(song_id)

        elif "album" in item["subject"]:
            album_id = notif_body.split("/Al/")[-1].split(")',")[0]
            logger.info(f"\t{item['subject']} https://vocadb.net/Al/{album_id}")

        elif "A new artist" in item["subject"]:
            # A new artist, '[sakkyoku645](https://vocadb.net/Ar/48199)', tagged with funk was just added.
            start, end = item["subject"].split("', tagged with ")
            artist_name, artist_url = start.split("](")
            artist_name = artist_name.split("[")[1]
            artist_url = artist_url.split(")")[0]
            tag_name = end.split(" was just")[0]
            logger.info(
                f"\tArtist tagged with '{tag_name}': {artist_name} {artist_url}"
            )

        else:
            logger.info(f"\t{notif_body}")

    if notification_ids:
        delete_notifications(session, USER_ID, notification_ids)
        save_file(NOTIF_LOG_FILE, notification_messages, append=True)

    logger.info(f"Found {len(new_song_ids)} new songs to check")
    return new_song_ids


def filter_out_seen_song_ids(seen_file: str, new_song_ids: list[str]) -> list[str]:
    """Filters seen song IDs out based on the seen song ids -file."""
    seen_song_ids = get_lines(seen_file)
    unseen_song_ids = []
    removed = 0

    for song_id in set(new_song_ids):
        if song_id in seen_song_ids:
            removed += 1
        else:
            unseen_song_ids.append(song_id)

    logger.info(f"Filtered out {removed}/{len(new_song_ids)} already seen ids.")
    return unseen_song_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id", type=int, help="VocaDB user id")
    parser.add_argument(
        "--include_read_notifications",
        action="store_true",
        help="Also check already read notifications",
    )
    parser.add_argument(
        "--max_songlist_length",
        default=200,
        type=int,
        help="Max songlist length (default 200)",
    )
    parser.add_argument(
        "--max_notifs",
        default=400,
        type=int,
        help="Max notifications to fetch (default)",
    )
    parser.add_argument(
        "--skip_covers",
        action="store_true",
        help="Skip covers that have original version as entry",
    )
    parser.add_argument(
        "--include_seen_songs",
        action="store_true",
        help="Include already seen songs in the songlist",
    )
    parser.add_argument(
        "--songlist_title",
        default="",
        type=str,
        help="Title of the songlist to create. Default is 'Songs to check (date)'",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    USER_ID = args.user_id
    INCLUDE_READ_NOTIFICATIONS = args.include_read_notifications
    MAX_SONGLIST_LENGTH = args.max_songlist_length
    MAX_NOTIFS = args.max_notifs
    SKIP_COVERS = args.skip_covers
    INCLUDE_SEEN = args.include_seen_songs
    SONGLIST_TITLE = args.songlist_title

    CREDENTIALS_FILE = "credentials.env"
    SEEN_SONG_IDS_FILE = "data/seen song ids.txt"
    NOTIF_LOG_FILE = "output/notifications.txt"

    un, pw = get_credentials(CREDENTIALS_FILE)
    login = {"userName": un, "password": pw}

    with requests.Session() as session:
        logger.info("Logging in...")
        login_attempt = session.post("https://vocadb.net/api/users/login", json=login)
        if login_attempt.status_code == 400:  # noqa: PLR2004
            logger.error("Login failed! Check your credentials.")
            sys.exit(1)
        else:
            logger.debug("Login successful!")

        all_notifications = fetch_notifications(
            USER_ID,
            session,
            include_read=INCLUDE_READ_NOTIFICATIONS,
            max_notifs=MAX_NOTIFS,
        )

        new_songs = filter_notifications(all_notifications, session, SKIP_COVERS)
        if not INCLUDE_SEEN:
            new_songs = filter_out_seen_song_ids(SEEN_SONG_IDS_FILE, new_songs)
        if not new_songs:
            logger.warning("No new songs found")
            sys.exit(0)
        if not SONGLIST_TITLE:
            date = str(datetime.datetime.now())[:10]  # YYYY-MM-DD
            songlist_title = f"Songs to check {date}"
        _ = input("Press enter to create the songlist(s)...")
        create_songlists(session, songlist_title, new_songs)
        save_file(SEEN_SONG_IDS_FILE, new_songs, append=True)
