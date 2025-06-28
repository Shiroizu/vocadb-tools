import time

from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_text

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


def export_songlist(songlist_id: int) -> str:
    text = fetch_text(f"{WEBSITE}/SongList/Export/{songlist_id}")
    _, _, table = text.partition("\n")  # remove header
    # notes;publishdate;title;url;pv.original.niconicodouga;pv.original.!niconicodouga;pv.reprint
    new_header = "songlist_notes;published;title;url;nico_pv;original_pv;reprint_pv"
    return new_header + "\n" + table


def parse_csv_songlist(csv: str, delimiter=";") -> list[list[str]]:
    return [line.split(delimiter) for line in csv.splitlines()]


def filter_songlist_ids_and_notes(songlist: list[list[str]]) -> dict[int, str]:
    notes_by_song_id = {}
    for songlist_entry in songlist[1:]:
        notes, _, _, url, _, _, _ = songlist_entry
        song_id = int(url.split("/S/")[-1])
        if song_id in notes_by_song_id:
            logger.warning(
                f"Song ID {song_id} already has a note: {notes_by_song_id[song_id]}"
            )
        notes_by_song_id[song_id] = notes

    return notes_by_song_id
