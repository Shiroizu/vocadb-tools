import requests

from vdbpy.api.users import USER_API_URL, logger


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
