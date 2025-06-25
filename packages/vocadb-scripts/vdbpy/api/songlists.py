import time

from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger

logger = get_logger()


def create_songlists(session, title, song_ids: list[str], max_length=200):
    """Create songlists on VocaDB with the given title and song IDs.

    Splits the list into sublists if over the max_length.
    """
    counter = 1

    for i in range(1 + len(song_ids) // max_length):
        sublist = song_ids[i * max_length : (i + 1) * max_length]
        if not sublist:
            break

        if len(song_ids) > max_length:
            logger.info(f"Posting sublist {counter}")

        else:
            logger.info("Posting songlist")

        songlist = {
            "songLinks": [],
            "author": {"id": 329},
            "name": f"{title} ({counter})",
        }
        counter += 1

        order = 1
        for song_id in sublist:
            sonlist_item = {"order": order, "song": {"id": int(song_id)}}
            songlist["songLinks"].append(sonlist_item)
            order += 1

        songlist_request = session.post(f"{WEBSITE}/api/songLists", json=songlist)
        songlist_request.raise_for_status()
        songlist_id = songlist_request.json()
        logger.info(f"Created songlist at {WEBSITE}/SongList/Details/{songlist_id}")

        time.sleep(3)
