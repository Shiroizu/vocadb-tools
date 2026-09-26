import os

# Override with VDBPY_WEBSITE (e.g. https://beta.vocadb.net) to target another instance.
WEBSITE = os.environ.get("VDBPY_WEBSITE", "https://vocadb.net").rstrip("/")
WIKI_URL = "https://wiki.vocadb.net"
LOCAL_WIKI_URL = "http://localhost:4321"

ACTIVITY_API_URL = f"{WEBSITE}/api/activityEntries"
ALBUM_API_URL = f"{WEBSITE}/api/albums"
ARTIST_API_URL = f"{WEBSITE}/api/artists"
COMMENT_API_URL = f"{WEBSITE}/api/comments"
ENTRY_REPORTS_URL = f"{WEBSITE}/api/admin/reports"
EVENT_API_URL = f"{WEBSITE}/api/releaseEvents"
PROFILE_URL = f"{WEBSITE}/Profile/"
SERIES_API_URL = f"{WEBSITE}/api/releaseEventSeries"
SONG_API_URL = f"{WEBSITE}/api/songs"
SONGLIST_API_URL = f"{WEBSITE}/api/songLists"
TAG_API_URL = f"{WEBSITE}/api/tags"
USER_API_URL = f"{WEBSITE}/api/users"
VENUE_API_URL = f"{WEBSITE}/api/venues"
