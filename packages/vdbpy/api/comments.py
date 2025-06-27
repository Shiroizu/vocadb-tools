from vdbpy.config import WEBSITE
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.network import fetch_totalcount


@cache_with_expiration(days=1000)
def get_comment_count(before_date: str) -> int:
    api_url = f"{WEBSITE}/api/comments"
    params = {"before": before_date}
    return fetch_totalcount(api_url, params=params)
