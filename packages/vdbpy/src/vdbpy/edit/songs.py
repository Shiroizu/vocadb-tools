import requests

from vdbpy.config import WEBSITE


def refresh_pv_metadata(session: requests.Session, song_id: int) -> None:
    """Refresh PV metadata for a song entry."""
    response = session.get(
        f"{WEBSITE}/Song/RefreshPVMetadatas/{song_id}", allow_redirects=False
    )
    location = response.headers.get("Location", "")
    if "/Login" in location:
        raise PermissionError("Moderator credentials required!")
