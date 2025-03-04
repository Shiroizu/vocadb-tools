from utils.cache import cache_with_expiration
from utils.network import fetch_totalcount


@cache_with_expiration(days=1000)
def get_edit_count(before_date: str) -> int:
    api_url = "https://vocadb.net/api/activityEntries"
    params = {"before": before_date}
    return fetch_totalcount(api_url, params=params)
