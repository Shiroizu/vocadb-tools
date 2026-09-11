import argparse
import sys
from datetime import datetime
from pathlib import Path

import requests

from vdbpy.api.notifications import (
    get_cached_notification_by_id,
    get_messages_by_user_id,
)
from vdbpy.api.users import find_user_by_username_1d
from vdbpy.config import WEBSITE
from vdbpy.utils.cache import get_vdbpy_cache_dir
from vdbpy.utils.files import get_credentials, sanitize_filename, save_file
from vdbpy.utils.logger import get_logger

logger = get_logger()

CREDENTIALS_FILE = "credentials.env"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Save your VocaDB private messages as markdown files."
            f" Credentials are read from '{CREDENTIALS_FILE}' in the current directory."
        )
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=None,
    )
    return parser.parse_args()


def cli() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir or get_vdbpy_cache_dir() / "dms"

    logger = get_logger("export_dms")

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

        _, user_id = find_user_by_username_1d(un)
        messages = get_messages_by_user_id(session, user_id)

        total = len(messages)
        counter = 1
        for message in messages:
            details = get_cached_notification_by_id(session, message["id"])
            subject: str = details["subject"]

            date = details["createdFormatted"]  # 2024/05/03 8:03
            parsed_date = datetime.strptime(date, "%Y/%m/%d %H:%M")  # noqa: DTZ007
            formatted_date = parsed_date.strftime("%Y-%m-%d %H-%M")

            receiver_id = details["receiver"]["id"]
            receiver_name = details["receiver"]["name"]
            sender_id = details["sender"]["id"]
            sender_name = details["sender"]["name"]

            recipient = sender_name if receiver_id == user_id else receiver_name
            recipient_id = sender_id if receiver_id == user_id else receiver_id

            direction = "TO" if sender_id == user_id else "FROM"

            filename = (
                f"{formatted_date} - {direction} '{recipient}' ({recipient_id}) "
                f" - {subject}"
            )
            logger.info(f"\n{counter}/{total}: From {sender_name} to {receiver_name}")
            logger.info(filename)
            counter += 1
            filename = sanitize_filename(filename)
            save_file(output_dir / f"{filename}.md", details["body"])

        logger.info(f"\nMessages saved to '{output_dir}'")


if __name__ == "__main__":
    cli()
