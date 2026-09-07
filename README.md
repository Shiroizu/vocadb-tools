# vocadb-tools

Python tooling for [VocaDB](https://vocadb.net/), as a single [uv](https://docs.astral.sh/uv/)
workspace.

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
uv run ruff check
uv run ty check
uv run pytest
```

## Tools

```
uv run vdb-sql --schema
uv run vdb-sql "SELECT id, song_type FROM songs LIMIT 5"
uv run vdb-export-dms
uv run vdb-export-rated-songs <user_id>
uv run vdb-notifs-to-songlist --help
```
