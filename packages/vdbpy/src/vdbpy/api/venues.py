from vdbpy.config import WEBSITE
from vdbpy.utils.network import fetch_json, fetch_json_items

VENUE_API_URL = f"{WEBSITE}/api/venues"

# TODO: Type VenueEntry


def get_venues(params):
    return fetch_json_items(VENUE_API_URL, params=params)


def get_venue(params):
    result = fetch_json(VENUE_API_URL, params=params)
    return result["items"][0] if result["items"] else {}


def get_venue_by_id(venue_id, fields=""):
    params = {"fields": fields} if fields else {}
    url = f"{VENUE_API_URL}/{venue_id}"
    return fetch_json(url, params=params)
