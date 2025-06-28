import sys
from datetime import datetime

import requests
from vdbpy.api.notifications import get_messages_by_user_id, get_notification_by_id
from vdbpy.api.users import find_user_by_username
from vdbpy.config import WEBSITE
from vdbpy.utils.files import get_credentials, sanitize_filename, save_file
from vdbpy.utils.logger import get_logger

logger = get_logger("export-dms")


if __name__ == "__main__":
    CREDENTIALS_FILE = "credentials.env"
    OUTPUT_DIR = "output/dms"

    un, pw = get_credentials(CREDENTIALS_FILE)
    login = {"userName": un, "password": pw}

    with requests.Session() as session:
        logger.info(f"Exporting notifications for user '{un}'")
        logger.info("Logging in...")
        login_attempt = session.post(f"{WEBSITE}/api/users/login", json=login)
        if login_attempt.status_code == 400:
            logger.error("Login failed! Check your credentials.")
            sys.exit(1)
        else:
            logger.debug("Login successful!")

        _, user_id = find_user_by_username(un)
        messages = get_messages_by_user_id(user_id, session)

        total = len(messages)
        counter = 1
        for message in messages:
            details = get_notification_by_id(session, message["id"])
            subject: str = details["subject"]

            date = details["createdFormatted"]  # 2024/05/03 8:03
            parsed_date = datetime.strptime(date, "%Y/%m/%d %H:%M")
            formatted_date = parsed_date.strftime("%Y-%m-%d %H-%M")

            receiver_id = details["receiver"]["id"]
            receiver_name = details["receiver"]["name"]
            sender_id = details["sender"]["id"]
            sender_name = details["sender"]["name"]

            recipient = sender_name if receiver_id == user_id else receiver_name
            recipient_id = sender_id if receiver_id == user_id else receiver_id

            direction = "TO" if sender_id == user_id else "FROM"

            filename = f"{formatted_date} - {direction} '{recipient}' ({recipient_id}) - {subject}"
            logger.info(f"\n{counter}/{total}: From {sender_name} to {receiver_name}")
            logger.info(filename)
            counter += 1
            filename = sanitize_filename(filename)
            save_file(f"{OUTPUT_DIR}/{filename}.md", details["body"])
