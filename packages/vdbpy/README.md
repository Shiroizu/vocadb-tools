![Coverage](coverage-badge.svg)

## About

Opinionated & type-safe Python wrapper library for working with https://github.com/VocaDB/vocadb API

Used for:
- https://github.com/Shiroizu/VocaDB-scripts
- Private mod scripts

## Usage

Installation with https://docs.astral.sh/uv/

- `uv add git+https://github.com/Shiroizu/VDBpy`

Upgrade to the most recent version with:

- `uv add --upgrade git+https://github.com/Shiroizu/VDBpy`

## Conventions

### File structure

- Function file locations are determined based on the return type instead of the API endpoint

### Cache

Function cache duration is seen from the function name:

```py
@cache_with_expiration(days=1)
def get_username_by_id_1d(user_id: int, include_usergroup=False) -> str:


@cache_without_expiration()
def get_cached_username_by_id(user_id: int, include_usergroup=False) -> str:
```

## TODO

TODO-count: 44

- [ ] Type-safe entry versions
    - [x] AlbumVersion
    - [x] ArtistVersion
    - [x] SongVersion
    - [x] TagVersion
    - [x] ReleaseEventVersion
    - [x] ReleaseEventSeriesVersion
    - [x] VenueVersion
    - [x] Simple tests
    - [ ] Full tests
- [ ] Type safe entries
    - [x] SongEntry (test progress 27/27)
    - [ ] AlbumEntry
    - [ ] ArtistEntry
    - [ ] TagEntry
    - [ ] ReleaseEventEntry
    - [ ] ReleaseEventSeriesEntry
    - [ ] VenueEntry
    - [ ] UserEntry
    - [ ] SongListEntry
    - [ ] Full tests