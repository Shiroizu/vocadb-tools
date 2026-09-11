# vocadb-tools

Python tooling for [VocaDB](https://vocadb.net/), as a single [uv](https://docs.astral.sh/uv/)
workspace (3 separate repos previously).

| Package | Import | Description |
|---|---|---|
| [packages/vdbpy](packages/vdbpy/) | `vdbpy` | Base library: API clients, parsers, types, dump handling |
| [packages/vocadb-rules](packages/vocadb-rules/) | `vocadb_rules` | Rule check modules, loaded by rule id |
| [packages/vocadb-scripts](packages/vocadb-scripts/) | `vocadb_scripts` | Scripts and CLI tools built on vdbpy |

The discord bot ([vocadb/mods](https://github.com/vocadb/mods)) is a separate private repo and
depends on all three.

## Usage

```
uv sync
uv run check     # ruff format --check + ruff check + ty check + pytest, stops at the first failure
```

Individually:

```
uv run ruff check
uv run ty check
uv run pytest
```

## Upgrading dependencies

```
uv tree --outdated --depth 1
uv lock --upgrade-package ruff --upgrade-package ty
uv lock --upgrade  # everything
```


## Testing

```
uv run pytest                   # < 1 sec
uv run pytest -m integration    # live VocaDB API
uv run pytest -m slow           # needs dump.zip
uv run pytest -m rules          # rule modules vs live entry versions
uv run pytest -m ""             # everything
```

The rule-module checks have additional CLI tests:

```
uv run python -m vocadb_rules.tests            # all rules + wiki crosscheck
uv run python -m vocadb_rules.tests --rule 55  # one rule + its dependencies
uv run python -m vocadb_rules.tests --debug
```

## Versioning

Each package keeps its own semver. `vcommit.py` bumps and commits the staged changes.

```
uv run vcommit.py patch "Fix a small bug"
uv run vcommit.py --package vdbpy minor "New API"  # bump this one, whatever is staged
uv run vcommit.py major "Breaking change"
```

All bumped versions go in the commit message: `vdbpy 23.3.0 + vocadb-tools 0.3.0, New API`.

## Tools

```
uv run vdb-sql --schema
uv run vdb-sql "SELECT id, song_type FROM songs LIMIT 5"
uv run vdb-export-dms
uv run vdb-export-rated-songs <user_id>
uv run vdb-notifs-to-songlist --help
```
