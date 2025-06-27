from vdbpy.config import WEBSITE
from vdbpy.utils.network import fetch_json, fetch_json_items


def fetch_notifications(
    user_id: int, session, include_read=False, max_notifs=400
) -> list[dict]:
    params = {
        "inbox": "Notifications",
        "unread": not include_read,
    }

    notif_url = f"{WEBSITE}/api/users/{user_id}/messages"
    return fetch_json_items(
        notif_url, session=session, params=params, max_results=max_notifs
    )


def get_notification_body(session, notification_id: int) -> str:
    notif_url = f"{WEBSITE}/api/users/messages/{notification_id}"
    return fetch_json(notif_url, session=session)["body"]
