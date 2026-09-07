![Coverage](coverage-badge.svg)

## About

Opinionated & type-safe Python wrapper library for working with https://github.com/VocaDB/vocadb API

Used for:
- [vocadb-scripts](../vocadb-scripts/) and [vocadb-rules](../vocadb-rules/), in this workspace
- Private mod scripts

## Usage

See the [workspace README](../../README.md).

Standalone usage with https://docs.astral.sh/uv/:

```toml
[tool.uv.sources]
vdbpy = { git = "https://github.com/Shiroizu/vocadb-tools", subdirectory = "packages/vdbpy" }
```

Upgrade to the most recent version with:

- `uv lock --upgrade-package vdbpy && uv sync`

To use a different VocaDB instance (e.g. beta), set the base URL before any vdbpy import. All of these work:

- Shell (session): `export VDBPY_WEBSITE=https://beta.vocadb.net` then run your script.
- One-off (single command): `VDBPY_WEBSITE=https://beta.vocadb.net uv run python your_script.py`

All API URLs and links are derived from this single value in `vdbpy.config`.

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


#### Coverage badge (WIP)

```bash
uv run coverage run -m pytest -v
uv run coverage xml
uv run genbadge coverage -i coverage.xml
```

^ TODO: Combine to one command

### Versioning

See the [workspace README](../../README.md#versioning).