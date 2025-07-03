import argparse
import datetime
import sys

import requests
from vdbpy.api.notifications import (
    delete_notifications,
    get_notification_by_id,
    get_notifications_by_user_id,
)
from vdbpy.api.songlists import create_songlists
from vdbpy.api.users import find_user_by_username
from vdbpy.config import WEBSITE
from vdbpy.utils.files import get_credentials, get_lines, save_file
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json

logger = get_logger("notifications_to_songlist")

def is_cover_with_original_as_entry(song_id: str) -> bool:
    url = f"{WEBSITE}/api/songs/{song_id}"
    entry = fetch_json(url)
    result = (entry["songType"] == "Cover") and ("originalVersionId" in entry)
    logger.debug(f"Song {song_id} is a cover with original as entry: {result}")
    return result


def filter_notifications(
    all_notifications, session: requests.Session, skip_covers=False, skip_music_pvs=False
) -> list[str]:
    """Returns a list of new song IDs from notifications."""
    notification_ids: list[str] = []
    notification_messages: list[str] = []
    new_song_ids: list[str] = []
    notification_messages = []
    counter = 0

    for item in all_notifications:
        notif_body: str = get_notification_by_id(session, item["id"])["body"]
        notification_messages.append(notif_body)

        counter += 1
        logger.debug(item)
        notif_body = notif_body.split("You're receiving this notification")[0]
        logger.info(f"{counter}/{len(all_notifications)} {notif_body}")

        # A new song tagged with electro drug https://vocadb.net/S/807206
        # A new song (original song) by AVTechNO! https://vocadb.net/S/807679
        # A new song (music pv) by MikitoP https://vocadb.net/S/807223
        # A new song (cover) by Reml https://vocadb.net/S/807220
        # A new song (original song) by Avaraya https://vocadb.net/S/807206
        # ...

        if not notif_body.startswith("New song "):
            logger.debug("Skipping non-song notification")
            continue

        song_id = notif_body.split("/S/")[-1].split(")',")[0].split("?")[0]
        logger.info(f"\t{item['subject']} {WEBSITE}/S/{song_id}")

        # Skip duplicate notifs
        if song_id in new_song_ids:
            logger.debug("Skipping dupe notification")
            continue

        if skip_covers and is_cover_with_original_as_entry(song_id):
            logger.info("\tSkipping cover song")
            continue

        if skip_music_pvs and notif_body.startswith("New song (music pv)"):
            logger.info("\tSkipping music PV")
            continue

        new_song_ids.append(song_id)
        continue

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
    # TODO --skip_out_of_scope songs
    # TODO --skip_instrumentals
    # TODO --skip_already_rated
    parser.add_argument(
        "--include_seen_songs",
        action="store_true",
        help="Include already seen songs in the songlist",
    )
    parser.add_argument(
        "--skip_music_pvs",
        action="store_true",
        help="Skip music pvs",
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

    INCLUDE_READ_NOTIFICATIONS = args.include_read_notifications
    MAX_SONGLIST_LENGTH = args.max_songlist_length
    MAX_NOTIFS = args.max_notifs
    SKIP_COVERS = args.skip_covers
    SKIP_MUSIC_PVS = args.skip_music_pvs
    INCLUDE_SEEN = args.include_seen_songs
    SONGLIST_TITLE = args.songlist_title

    CREDENTIALS_FILE = "credentials.env"
    SEEN_SONG_IDS_FILE = "data/seen song ids.txt"
    NOTIF_LOG_FILE = "output/notifications.txt"

    un, pw = get_credentials(CREDENTIALS_FILE)
    login = {"userName": un, "password": pw}

    _, USER_ID = find_user_by_username(un)

    logger.info(f"Fetching notifications for user {un} ({USER_ID}) with settings:\n")
    logger.info(
        f"\t{INCLUDE_READ_NOTIFICATIONS=} (change with --include_read_notifications)"
    )
    logger.info(f"\t{MAX_SONGLIST_LENGTH=} (change with --max_songlist_length N)")
    logger.info(f"\t{MAX_NOTIFS=} (change with --max_notifs N)")
    logger.info(f"\t{SKIP_COVERS=} (change with --skip_covers)")
    logger.info(f"\t{SKIP_MUSIC_PVS=} (change with --skip_music_pvs)")
    logger.info(f"\t{INCLUDE_SEEN=} (change with --include_seen_songs)")
    logger.info(f"\t{SONGLIST_TITLE=} (change with --songlist_title S)")

    _ = input("\nPress enter to continue...")

    with requests.Session() as session:
        logger.info("Logging in...")
        login_attempt = session.post(f"{WEBSITE}/api/users/login", json=login)
        if login_attempt.status_code == 400:
            logger.error("Login failed! Check your credentials.")
            sys.exit(1)
        else:
            logger.debug("Login successful!")

        all_notifications = get_notifications_by_user_id(
            USER_ID,
            session,
            include_read=INCLUDE_READ_NOTIFICATIONS,
            max_notifs=MAX_NOTIFS,
        )

        new_songs = filter_notifications(all_notifications, session, SKIP_COVERS, SKIP_MUSIC_PVS)
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
