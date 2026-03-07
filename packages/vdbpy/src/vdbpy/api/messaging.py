from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import requests

from vdbpy.api.users import USER_API_URL, logger
from vdbpy.types.users import UserGroup
from vdbpy.utils.date import parse_date
from vdbpy.utils.network import fetch_json

Inbox = Literal["Received", "Sent"]


@dataclass
class ModMessage:
    id: int
    body: str
    subject: str
    created: datetime
    target_user_id: int
    target_user_name: str
    target_user_group: UserGroup
    target_avatar: str
    high_priority: bool
    inbox: Inbox


def _parse_mod_message(data: dict[str, Any], inbox: Inbox) -> ModMessage:
    other = data["sender"] if inbox == "Received" else data["receiver"]
    return ModMessage(
        id=data["id"],
        body=data["body"],
        subject=data["subject"],
        created=parse_date(data["createdFormatted"]),
        target_user_id=other["id"],
        target_user_name=other["name"],
        target_user_group=other["groupId"],
        high_priority=data["highPriority"],
        target_avatar=other["mainPicture"]["urlTinyThumb"]
        if "mainPicture" in other
        else "",
        inbox=inbox,
    )


def get_user_messages(
    session: requests.Session,
    user_id: str,
    include_unread: bool = True,
    max_results: int = 20,
) -> list[ModMessage]:
    """Retrieve sent and received messages for a user."""
    logger.info(f"Fetching sent and received messages for {user_id}")
    mod_messages: list[ModMessage] = []

    for inbox in ("Received", "Sent"):
        url = f"{USER_API_URL}/{user_id}/messages"
        params = {
            "inbox": inbox,
            "unread": "false" if include_unread else "true",
            "maxResults": str(max_results),
        }
        result = session.get(url, params=params).json()
        for item in result["items"]:
            mod_messages.append(_parse_mod_message(item, inbox))

    mod_messages.sort(key=lambda x: x.id)
    return mod_messages


def get_sent_messages_to(
    session: requests.Session,
    sender_id: str,
    target_user_id: int,
    subject: str | None = None,
    max_results: int = 20,
) -> list[ModMessage]:
    """Return sent messages addressed to a specific recipient."""
    params: dict[str, Any] = {
        "inbox": "Sent",
        "unread": "false",
        "maxResults": max_results,
        "getTotalCount": "false",
        "anotherUserId": target_user_id,
    }
    result = session.get(f"{USER_API_URL}/{sender_id}/messages", params=params).json()
    messages: list[ModMessage] = []
    for item in result["items"]:
        if subject is not None and item["subject"] != subject:
            continue
        messages.append(_parse_mod_message(item, "Sent"))
    return messages


def get_message_body(session: requests.Session, message_id: int) -> str:
    """Retrieve the body text of a single message."""
    json = fetch_json(f"{USER_API_URL}/messages/{message_id}", session=session)
    if not json or "body" not in json:
        return ""
    return json["body"]


def send_message(
    session: requests.Session,
    receiver: str,
    subject: str,
    message: str,
    sender_id: int,
    prompt: bool = True,
) -> None:
    url = f"{USER_API_URL}/{sender_id}/messages"

    data = {
        "body": message,
        "highPriority": False,
        "receiver": {"name": receiver},
        "sender": {"id": sender_id},
        "subject": subject,
    }

    if prompt:
        msg = f"{'' * 39}\nTO='{receiver}' SUBJECT='{subject}'\n{message}\n{'-' * 39}"
        logger.info(msg)

        _ = input("Press enter to send...")
    message_request = session.post(url, json=data)
    message_request.raise_for_status()
