from typing import Literal

import requests

from vdbpy.config import COMMENT_API_URL, WEBSITE
from vdbpy.types.shared import Comment, EntryType
from vdbpy.utils.data import add_s, get_monthly_count
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_all_items_between_dates,
    fetch_json,
)

logger = get_logger()


def get_comments_by_user_id(user_id: int) -> list[Comment]:
    logger.debug(f"Fetching all comments for user id {user_id}")
    a = str(parse_date(get_the_oldest_comment_by_user_id(user_id)["created"])).split()[
        0
    ]
    b = str(
        parse_date(get_the_most_recent_comment_by_user_id(user_id)["created"])
    ).split()[0]
    logger.info(f"\nOldest comment date is {a}")
    logger.info(f"Most recent comment date is {b}\n")
    params = {"userId": user_id, "fields": "entry"}
    all_comments = fetch_all_items_between_dates(
        COMMENT_API_URL, since=a, before=b, params=params, date_indicator="created"
    )[0]
    logger.info(f"Found {len(all_comments)} comments by {user_id}")
    return all_comments


def get_monthly_comment_count(year: int, month: int) -> int:
    return get_monthly_count(year, month, COMMENT_API_URL)


def get_the_most_recent_comment_by_user_id(user_id: int = 0) -> Comment:
    params = {
        "userId": user_id,
        "sortRule": "CreateDateDescending",
        "maxResults": 1,
        "fields": "Entry",
    }
    return fetch_json(COMMENT_API_URL, params=params)["items"][0]


def get_the_oldest_comment_by_user_id(user_id: int = 0) -> Comment:
    params = {
        "userId": user_id,
        "sortRule": "CreateDate",
        "maxResults": 1,
        "fields": "Entry",
    }
    return fetch_json(COMMENT_API_URL, params=params)["items"][0]


def remove_comment_by_id(
    session: requests.Session, entry_type: EntryType | Literal["User"], comment_id: int
) -> bool:
    url = f"{WEBSITE}/api/{add_s(entry_type)}/comments/{comment_id}"
    if entry_type == "User":
        url = f"{WEBSITE}/api/users/profileComments/{comment_id}"

    logger.info(f"DELETION URL {url}")
    deletion_attempt = None
    try:
        deletion_attempt = session.delete(url)
        deletion_attempt.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.warning(f"Comment {comment_id} could not be deleted.")
        if deletion_attempt:
            logger.warning(f"{deletion_attempt.status_code}: {deletion_attempt.text}")
        return False

    logger.info("Comment deleted.")
    return True


def remove_all_comments_by_user_id(
    session: requests.Session, user_id: int, prompt_interval: int = 1
) -> int:
    all_comments = get_comments_by_user_id(user_id)
    counter = 0
    for comment in all_comments:
        author_name = comment["author"]["name"]
        entry_type = comment["entry"]["entryType"]
        entry_id = comment["entry"]["id"]
        entry_name = comment["entry"]["name"]
        comment_id = comment["id"]
        comment_content = comment["message"]
        logger.info(f"\nDeleting comment id {comment_id} by {author_name},")
        logger.info(f"{entry_type} entry {entry_id} f'({entry_name})':")
        logger.info(f"\t'{comment_content}'")

        if prompt_interval > 0 and counter % prompt_interval == 0:
            _ = input("Press enter to delete comment.")

        removed = remove_comment_by_id(session, entry_type, comment_id)
        if removed:
            counter += 1

    logger.info(f"Deleted {counter} comments out of {len(all_comments)} for {user_id}")
    return counter
