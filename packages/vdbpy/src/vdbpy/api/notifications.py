import requests

from vdbpy.config import WEBSITE
from vdbpy.utils.cache import cache_with_expiration, cache_without_expiration
from vdbpy.utils.data import split_list
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json, fetch_json_items

logger = get_logger()

USERS_API_URL = f"{WEBSITE}/api/users"


@cache_without_expiration()
def get_notification_by_id(session, notification_id: int) -> dict:
    notif_url = f"{USERS_API_URL}/messages/{notification_id}"
    return fetch_json(notif_url, session=session)


def get_messages_by_user_id(
    session, user_id: int, include_sent=True, include_received=True, max_results=50
) -> list[dict]:
    notif_url = f"{USERS_API_URL}/{user_id}/messages"

    received = (
        fetch_json_items(
            notif_url,
            session=session,
            params={"inbox": "Received"},
            max_results=max_results,
        )
        if include_received
        else []
    )
    sent = (
        fetch_json_items(
            notif_url,
            session=session,
            params={"inbox": "Sent"},
            max_results=max_results,
        )
        if include_sent
        else []
    )

    return received + sent


@cache_with_expiration(days=1)
def get_notifications_by_user_id(
    user_id: int, session, include_read=False, max_notifs=400
) -> list[dict]:
    notif_url = f"{USERS_API_URL}/{user_id}/messages"
    params = {
        "inbox": "Notifications",
        "unread": not include_read,
    }
    return fetch_json_items(
        notif_url, session=session, params=params, max_results=max_notifs
    )


def delete_notifications(
    session: requests.Session, user_id: int, notification_ids: list[int]
):
    logger.info(f"Got total of {len(notification_ids)} notifications to delete.")
    for sublist in split_list(notification_ids):
        deletion_url = f"{USERS_API_URL}/{user_id}/messages?"
        query = [f"messageId={notif_id}" for notif_id in sublist]
        deletion_url += "&".join(query)
        _ = input(f"Press enter to delete {len(sublist)} notifications")
        deletion_request = session.delete(deletion_url)
        deletion_request.raise_for_status()
