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

## Dev

- Lint: `uv run ty check`
- Format: `uv run ruff check`

### Testing

Tests are split into **unit** (no network) and **integration** (VocaDB API).

```bash
uv run pytest tests/unit/
uv run pytest -m integration
uv run pytest
```

^ TODO: Command for rerunning only the failed tests

#### Coverage badge

```bash
uv run coverage run -m pytest -v
uv run coverage xml
uv run genbadge coverage -i coverage.xml
```

^ TODO: Combine to one command

```
uv run coverage run -m pytest -v
==== test session starts ====
platform linux -- Python 3.13.9, pytest-9.0.2, pluggy-1.6.0 -- 
cachedir: .pytest_cache
rootdir: /home/.../VDBPY
configfile: pyproject.toml
testpaths: tests
plugins: mock-3.15.1
collected 99 items                                                                                                  

tests/integration/test_edits_integration.py::test_future_edit PASSED                                          [  1%]
tests/integration/test_edits_integration.py::test_last_10_yesterday_edits_with_no_save_dir PASSED             [  2%]
...
tests/unit/test_utils_date.py::test_parse_date_short_format PASSED                                            [100%]
==== 99 passed in 201.49s (0:03:21) ====
```


### Versioning

Commit the staged changes with automatic version bump:

```bash
uv run vcommit.py patch "Fix a small bug"
```