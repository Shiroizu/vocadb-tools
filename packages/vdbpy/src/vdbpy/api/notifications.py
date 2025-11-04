from typing import Any

import requests

from vdbpy.config import USER_API_URL
from vdbpy.utils.cache import cache_without_expiration
from vdbpy.utils.data import split_list
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json, fetch_json_items

logger = get_logger()

type Notification = dict[Any, Any]  # TODO implement


@cache_without_expiration()
def get_cached_notification_by_id(
    session: requests.Session, notification_id: int
) -> Notification:
    notif_url = f"{USER_API_URL}/messages/{notification_id}"
    return fetch_json(notif_url, session=session)


def get_messages_by_user_id(
    session: requests.Session,
    user_id: int,
    include_sent: bool = True,
    include_received: bool = True,
    max_results: int = 50,
) -> list[Notification]:
    notif_url = f"{USER_API_URL}/{user_id}/messages"

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


def get_notifications_by_user_id(
    user_id: int,
    session: requests.Session,
    include_read: bool = False,
    max_notifs: int = 400,
) -> list[Notification]:
    notif_url = f"{USER_API_URL}/{user_id}/messages"
    params = {
        "inbox": "Notifications",
        "unread": not include_read,
    }
    return fetch_json_items(
        notif_url, session=session, params=params, max_results=max_notifs
    )


def delete_notifications(
    session: requests.Session, user_id: int, notification_ids: list[int]
) -> int:
    counter = 0
    logger.info(f"Got total of {len(notification_ids)} notifications to delete.")
    for sublist in split_list(notification_ids):
        deletion_url = f"{USER_API_URL}/{user_id}/messages?"
        query = [f"messageId={notif_id}" for notif_id in sublist]
        deletion_url += "&".join(query)
        _ = input(f"Press enter to delete {len(sublist)} notifications")
        deletion_request = session.delete(deletion_url)
        deletion_request.raise_for_status()
        counter += 1
    return counter
