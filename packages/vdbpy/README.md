## About

Python library for working with https://github.com/VocaDB/vocadb

Used for:
- https://github.com/Shiroizu/VocaDB-scripts
- Private mod scripts

## Usage

Installation with https://docs.astral.sh/uv/

- `uv add git+https://github.com/Shiroizu/VDBpy`

Upgrade to the most recent version with:

- `uv add --upgrade git+https://github.com/Shiroizu/VDBpy`

## Code

### File structure

Functions are separated by return type instead of the API endpoint:

```py
# api/songs
def get_song_entries_by_songlist_id(songlist_id: int, params=None) -> list[Song]:
    url = f"{SONGLIST_API_URL}/{songlist_id}/songs"
```

### Cache

Function cache duration is seen from the function name:

```py
@cache_with_expiration(days=1)
def get_username_by_id_1d(user_id: int, include_usergroup=False) -> str:


@cache_without_expiration()
def get_cached_username_by_id(user_id: int, include_usergroup=False) -> str:
```

## TODO

- [x] Consistent cache usage
- [x] Consolidate API URLS to `config.py`
- [ ] Full types
    - [ ] Simple entry data
    - [ ] Simple entry data cached by version id
    - [ ] Full entry data (fields=All)
    - [ ] Entry details
- [ ] Comprehensive unit tests & coverage badge
- [ ] Remove redundant fetch_json calls