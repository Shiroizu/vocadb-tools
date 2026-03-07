import requests

from vdbpy.config import WEBSITE


def add_song_to_list(
    session: requests.Session, list_id: str, song_id: str
) -> None:
    """Add a single song to an existing songlist via the MVC endpoint."""
    params = {
        "listId": list_id,
        "songId": song_id,
        "notes": "",
        "newListName": "",
    }
    session.post(f"{WEBSITE}/Song/AddSongToList", params=params).raise_for_status()
