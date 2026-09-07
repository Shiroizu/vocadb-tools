Collection of [VocaDB](https://vocadb.net/) related scripts.

Uses [vdbpy](../vdbpy/) under the hood.

Ideas, Pull Requests, etc. are welcome.

## Screenshots

<img width="472" height="397" alt="Untitled" src="https://github.com/user-attachments/assets/d69a29f4-e889-4a6c-8b6d-b63d69c614c1" />

## Usage

1) Install [Git](https://git-scm.com/downloads) --> `git clone https://github.com/Shiroizu/vocadb-tools` (or download ZIP & extract)

2) `cd vocadb-tools`

3) Install [uv](https://docs.astral.sh/uv/)

4) Run commands with "uv run", from the workspace root:

```
uv run vdb-sql --schema
uv run packages/vocadb-scripts/src/vocadb_scripts/graph/monthly_comments.py
```