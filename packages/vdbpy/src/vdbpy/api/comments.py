from vdbpy.config import WEBSITE
from vdbpy.types import Entry_type
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.data import add_s
from vdbpy.utils.date import parse_date
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import (
    fetch_all_items_between_dates,
    fetch_json,
    fetch_totalcount,
)

logger = get_logger()


def get_the_most_recent_comment(user_id=0):
    url = f"{WEBSITE}/api/comments"
    params = {
        "userId": user_id,
        "sortRule": "CreateDateDescending",
        "maxResults": 1,
        "fields": "Entry",
    }
    return fetch_json(url, params=params)["items"][0]


def get_the_oldest_comment(user_id=0):
    url = f"{WEBSITE}/api/comments"
    params = {
        "userId": user_id,
        "sortRule": "CreateDate",
        "maxResults": 1,
        "fields": "Entry",
    }
    return fetch_json(url, params=params)["items"][0]


def get_comments_by_user_id(user_id) -> list:
    logger.debug(f"Fetching all comments for user id {user_id}")
    a = str(parse_date(get_the_oldest_comment(user_id)["created"])).split()[0]
    b = str(parse_date(get_the_most_recent_comment(user_id)["created"])).split()[0]
    logger.info(f"\nOldest comment date is {a}")
    logger.info(f"Most recent comment date is {b}\n")
    url = f"{WEBSITE}/api/comments"
    params = {"userId": user_id, "fields": "entry"}
    all_comments = fetch_all_items_between_dates(
        url, a, b, params=params, date_indicator="created"
    )
    logger.info(f"Found {len(all_comments)} comments by {user_id}")
    return all_comments


@cache_with_expiration(days=1000)
def get_comment_count(before_date: str) -> int:
    api_url = f"{WEBSITE}/api/comments"
    params = {"before": before_date}
    return fetch_totalcount(api_url, params=params)


def remove_comment_by_id(session, entry_type: Entry_type, comment_id: int):
    url = f"{WEBSITE}/api/{add_s(entry_type)}/comments/{comment_id}"
    logger.info(f"DELETION URL {url}")
    deletion_attempt = session.delete(url)
    deletion_attempt.raise_for_status()
    logger.info("Comment deleted.")


def remove_all_comments_by_user_id(session, user_id: int, prompt_interval=1):
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
            counter += 1
        remove_comment_by_id(session, entry_type, comment_id)

    logger.info(f"Deleted {len(all_comments)} comments by {user_id}")
