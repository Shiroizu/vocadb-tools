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
