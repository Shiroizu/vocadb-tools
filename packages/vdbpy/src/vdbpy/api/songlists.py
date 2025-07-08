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


def export_songlist(songlist_id: int) -> list[str]:
    text = fetch_text(f"{WEBSITE}/SongList/Export/{songlist_id}").splitlines()
    # notes;publishdate;title;url;pv.original.niconicodouga;pv.original.!niconicodouga;pv.reprint
    table_without_header = text[1:]
    new_header = "songlist_notes;published;title;url;nico_pv;original_pv;reprint_pv"
    return [new_header, *table_without_header]


def parse_csv_songlist(csv: list[str], delimiter=";") -> list[list[str]]:
    lines = [line.split(delimiter) for line in csv if line.strip()]
    logger.debug(f"Parsing csv of length {len(csv)}. First lines: {csv[:2]}")
    for line in lines[1:]:
        extra_length = len(line) - 7
        if extra_length:
            # Title contains delimiter chars
            # ['127 537 views', '1/26/2023', '"PLS (-__-', ')"', 'https://vocadb.net/S/471057', '', 'https://youtu.be/CMPfzVbEX4E', '']
            logger.warning("Exported CSV contains title with delimiter chars:")
            logger.warning(line)
            # Merge items starting from index 2:
            fixed_line = line[:2] + line[2 : 2 + extra_length] + line[-4:]
            logger.info(f"Fixed line (len={len(fixed_line)}) is:")
            assert len(fixed_line) == 7  # noqa: S101
            lines[lines.index(line)] = fixed_line
    return lines
