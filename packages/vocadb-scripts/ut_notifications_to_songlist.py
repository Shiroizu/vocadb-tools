import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
from vdbpy.api.notifications import (
    Notification,
    delete_notifications,
    get_cached_notification_by_id,
)
from vdbpy.api.songlists import (
    create_songlists_with_size_limit,
    export_songlist,
    parse_csv_songlist,
)
from vdbpy.api.songs import get_song_by_id
from vdbpy.api.users import find_user_by_username_1d
from vdbpy.config import WEBSITE
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.files import get_credentials, get_lines, save_file
from vdbpy.utils.logger import get_logger

logger = get_logger()

# TODO --skip_out_of_scope songs
# TODO --skip_already_rated
# TODO unplayable media (bandcamp)
# TODO pass options as a dict


@cache_with_expiration(days=1)
def is_cover_with_original_as_entry(song_id: int) -> bool:
    entry = get_song_by_id(song_id)
    result = (entry.song_type == "Cover") and (entry.original_version_id > 0)
    if result:
        logger.info(f"\t  Cover of {WEBSITE}/S/{entry.original_version_id}, skipping.")
    return result


def is_instrumental(song_id: int) -> bool:
    entry = get_song_by_id(song_id, fields={"artists"})
    assert entry.artists != "Unknown"  # noqa: S101
    for artist in entry.artists:
        if artist.entry == "Custom artist":
            continue
        if "Vocalist" in artist.categories or "Vocalist" in artist.effective_roles:
            return False
    return True


def filter_notifications(
    user_id: int,
    all_notifications: list[Notification],
    session: requests.Session,
    skip_covers: bool = False,
    skip_music_pvs: bool = False,
    skip_instruments: bool = False,
    delete_seen_notifs: bool = False,
) -> list[int]:
    """Return a list of new song IDs from notifications."""
    notification_messages: list[str] = []
    new_song_ids: list[int] = []
    counter = 0

    for item in all_notifications:
        notif_body: str = get_cached_notification_by_id(session, item["id"])["body"]
        notification_messages.append(notif_body)

        counter += 1
        logger.debug(item)
        notif_body = notif_body.split("You're receiving this notification", maxsplit=1)[
            0
        ]
        logger.debug(f"{counter}/{len(all_notifications)} {notif_body}")

        # A new song tagged with electro drug https://vocadb.net/S/807206
        # A new song (original song) by AVTechNO! https://vocadb.net/S/807679
        # A new song (music pv) by MikitoP https://vocadb.net/S/807223
        # A new song (cover) by Reml https://vocadb.net/S/807220
        # A new song (original song) by Avaraya https://vocadb.net/S/807206
        # ...

        if not notif_body.startswith("A new song"):
            logger.debug("Skipping non-song notification")
            continue

        song_id = int(notif_body.split("/S/")[-1].split(")',")[0].split("?")[0])
        logger.info(
            f"\t{counter}/{len(all_notifications)} {item['subject']} "
            f"{WEBSITE}/S/{song_id}"
        )

        # Skip duplicate notifs
        if song_id in new_song_ids:
            logger.info("Skipping dupe notification")
            continue

        if skip_covers and is_cover_with_original_as_entry(song_id):
            logger.info("\t\tSkipping cover song ")
            continue

        if skip_instruments and is_instrumental(song_id):
            logger.info("\t\tSkipping instrumental song ")
            continue

        if skip_music_pvs and notif_body.startswith("New song (music pv)"):
            logger.info("\tSkipping music PV")
            continue

        # delete_notifications(session, USER_ID, notification_ids)
        new_song_ids.append(song_id)
        continue

    save_file(NOTIF_LOG_FILE, notification_messages, append=True)
    if delete_seen_notifs:
        logger.info("Deleting seen notificatoins...")
        delete_notifications(
            session=session,
            user_id=user_id,
            notification_ids=[item["id"] for item in all_notifications],
        )

    logger.info(f"\nFound {len(new_song_ids)} new songs based on notifications.")
    return new_song_ids


def filter_out_seen_song_ids(seen_file: Path, new_song_ids: list[int]) -> list[int]:
    """Filter out seen song IDs out based on the seen song ids -file."""
    seen_song_ids_set = set(map(int, get_lines(seen_file)))
    new_song_ids_set = set(new_song_ids)
    unseen_song_ids = list(new_song_ids_set - seen_song_ids_set)
    number_of_removed_ids = len(new_song_ids_set) - len(unseen_song_ids)

    logger.info(
        f"Filtered {number_of_removed_ids}/{len(new_song_ids_set)} already seen ids."
    )
    return unseen_song_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include_read_notifications",
        "-ir",
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
        "--include_seen_songs",
        "-is",
        action="store_true",
        help="Include already seen songs in the songlist",
    )

    parser.add_argument(
        "--skip_covers",
        "-sc",
        action="store_true",
        help="Skip covers that have original version as entry",
    )

    parser.add_argument(
        "--skip_instrumentals",
        "-si",
        action="store_true",
        help="Skip instrumental songs (no vocals)",
    )

    parser.add_argument(
        "--skip_music_pvs",
        "-sm",
        action="store_true",
        help="Skip music pvs",
    )

    parser.add_argument(
        "--songlist_title",
        default="",
        type=str,
        help="Title of the songlist to create. Default is 'Songs to check (date)'",
    )

    parser.add_argument(
        "--delete_seen_notifications",
        "-ds",
        action="store_true",
        help="Delete seen notifications.",
    )

    return parser.parse_args()


def get_songlist_song_ids(songlist_id: int) -> list[int]:
    rows = parse_csv_songlist(export_songlist(songlist_id))
    song_ids: list[int] = []
    for row in rows[1:]:
        entry_url = row[3]
        song_ids.append(int(entry_url.split("/S/")[-1]))
    return song_ids


if __name__ == "__main__":
    logger = get_logger("notifications_to_songlist")
    args = parse_args()

    INCLUDE_READ_NOTIFICATIONS = args.include_read_notifications
    MAX_SONGLIST_LENGTH = args.max_songlist_length
    MAX_NOTIFS = args.max_notifs
    SKIP_COVERS = args.skip_covers
    SKIP_INSTRUMENTALS = args.skip_instrumentals
    SKIP_MUSIC_PVS = args.skip_music_pvs
    INCLUDE_SEEN_SONGS = args.include_seen_songs
    DELETE_SEEN_NOTIFS = args.delete_seen_notifications
    SONGLIST_TITLE = args.songlist_title

    CREDENTIALS_FILE = "credentials.env"
    SEEN_SONG_IDS_FILE = Path("data") / "seen song ids.txt"
    NOTIF_LOG_FILE = Path("output") / "notifications.txt"

    un, pw = get_credentials(CREDENTIALS_FILE)
    login = {"userName": un, "password": pw}

    _, USER_ID = find_user_by_username_1d(un)

    songlist_title = (
        SONGLIST_TITLE or f"Songs to check {str(datetime.now(tz=UTC))[:10]}"
    )

    logger.info(f"Fetching notifications for user {un} ({USER_ID}) with settings:\n")
    logger.info(
        f"\t{INCLUDE_READ_NOTIFICATIONS=} (change with --include_read_notifications)"
    )
    logger.info(f"\t{MAX_SONGLIST_LENGTH=} (change with --max_songlist_length N)")
    logger.info(f"\t{MAX_NOTIFS=} (change with --max_notifs N)")
    logger.info(f"\t{SKIP_COVERS=} (change with --skip_covers or -sc)")
    logger.info(f"\t{SKIP_MUSIC_PVS=} (change with --skip_music_pvs or -sm)")
    logger.info(f"\t{SKIP_INSTRUMENTALS=} (change with --skip_instruments or -si)")
    logger.info(f"\t{INCLUDE_SEEN_SONGS=} (change with --include_seen_songs or -is)")
    logger.info(
        f"\t{INCLUDE_READ_NOTIFICATIONS=} "
        "(change with --include_read_notifications or -ir)"
    )
    logger.info(
        f"\t{DELETE_SEEN_NOTIFS=} (change with --delete_seen_notifications or -ds)"
    )
    logger.info(f"\t{songlist_title=} (change with --songlist_title S)")

    _ = input("\nPress enter to continue...")

    with requests.Session() as session:
        logger.info("Logging in...")
        login_attempt = session.post(f"{WEBSITE}/api/users/login", json=login)
        if login_attempt.status_code == 400:
            logger.error("Login failed! Check your credentials.")
            sys.exit(1)
        else:
            logger.debug("Login successful!")

        _ = set(map(int, get_lines(SEEN_SONG_IDS_FILE)))
        """
        all_notifications = get_notifications_by_user_id(
            USER_ID,
            session,
            include_read=INCLUDE_READ_NOTIFICATIONS,
            max_notifs=MAX_NOTIFS,
        )
        logger.info(f"Found {len(all_notifications)} notifications")

        new_song_ids = filter_notifications(
            user_id=USER_ID,
            session=session,
            all_notifications=all_notifications,
            skip_covers=SKIP_COVERS,
            skip_music_pvs=SKIP_MUSIC_PVS,
            skip_instruments=SKIP_INSTRUMENTALS,
            delete_seen_notifs=DELETE_SEEN_NOTIFS,
        )

        """

        from vdbpy.api.songs import SongSearchParams, get_songs

        song_entries = get_songs(
            song_search_params=SongSearchParams(release_event_id=9122)
        )
        new_song_ids = [entry.id for entry in song_entries]

        logger.info(f"{len(new_song_ids)}")

        if not INCLUDE_SEEN_SONGS:
            new_song_ids = filter_out_seen_song_ids(SEEN_SONG_IDS_FILE, new_song_ids)

        logger.info(f"{len(new_song_ids)}")

        if not new_song_ids:
            logger.warning("No new songs found")
            sys.exit(0)
        _ = input("Press enter to create the songlist(s)...")
        create_songlists_with_size_limit(
            session=session,
            song_ids=new_song_ids,
            author_id=USER_ID,
            title="Anon3 songs to check",
        )
        save_file(SEEN_SONG_IDS_FILE, new_song_ids, append=True)
        logger.info(f"Notifications appended to '{SEEN_SONG_IDS_FILE}'")
