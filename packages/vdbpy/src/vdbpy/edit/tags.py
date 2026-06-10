import requests

from vdbpy.config import WEBSITE
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_with_retries

logger = get_logger()


def remove_song_tag_usage(session: requests.Session, tag_usage_id: int) -> None:
    """Remove a tag usage from a song entirely (moderator action)."""
    url = f"{WEBSITE}/api/users/current/songTags/{tag_usage_id}"
    logger.info(f"Removing song tag usage {tag_usage_id}")
    fetch_with_retries(url=url, verb="delete", session=session)
