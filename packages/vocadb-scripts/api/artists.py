from utils.cache import cache_with_expiration
from utils.network import fetch_json


@cache_with_expiration(days=1000)
def get_base_voicebank(artist_id: int, recursive=True):
    """Get base voicebank id if it exists. Return current id otherwise."""
    params = {"fields": "baseVoiceBank"}
    next_base_vb_id = artist_id
    while True:
        url = f"https://vocadb.net/api/artists/{next_base_vb_id}"
        next_base_vb = fetch_json(url, params=params)
        if "baseVoicebank" in next_base_vb and recursive:
            next_base_vb_id = next_base_vb["baseVoicebank"]["id"]
            continue
        return next_base_vb


def get_artist(artist_id, fields=""):
    params = {"fields": fields} if fields else {}
    url = f"https://vocadb.net/api/artists/{artist_id}"
    """
    artistType	"Producer"
    createDate	"2011-05-13T18:41:41"
    defaultName	"Clean Tears"
    defaultNameLanguage	"English"
    id	20
    name	"Clean Tears"
    pictureMime	"image/jpeg"
    status	"Approved"
    version	38
    """
    return fetch_json(url, params=params)
