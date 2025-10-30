from vdbpy.api.users import USER_API_URL, logger


def send_message(
    session,
    receiver_username: str,
    subject: str,
    message: str,
    sender_id: int,
    prompt=True,
) -> None:
    url = f"{USER_API_URL}/{sender_id}/messages"

    data = {
        "body": message,
        "highPriority": False,
        "receiver": {"name": receiver_username},
        "sender": {"id": sender_id},
        "subject": subject,
    }

    if prompt:
        logger.info(
            f"{'---' * 10}\nTO='{receiver_username}' SUBJECT='{subject}'\n{message}\n{'---' * 10}"
        )

        _ = input("Press enter to send...")
    message_request = session.post(url, json=data)
    message_request.raise_for_status()
