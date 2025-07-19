from vdbpy.config import WEBSITE
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.network import fetch_json

EVENT_API_URL = f"{WEBSITE}/api/releaseEvents"

# TODO: Type EventEntry


@cache_with_expiration(days=1)
def get_event_details_by_event_id(event_id: int, params=None):
    params = {} if params is None else params
    api_url = f"{EVENT_API_URL}/releaseEvents/{event_id}"
    """ Example https://vocadb.net/api/releaseEvents/3000
    category	"Unspecified"
    date	"2024-02-14T00:00:00Z"
    endDate	"2024-02-17T00:00:00Z" (optional)
    id	3000
    name	"KAITO誕生祭 2024"
    seriesId	14
    seriesNumber	2024
    seriesSuffix	""
    status	"Finished"
    urlSlug	"kaitos-birthday-2024"
    venueName	""
    version	15
    """
    return fetch_json(api_url, params=params)
