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
uv run vdb-graph-monthly-comments
```

Add `--help` to any command for its arguments.

### Commands

Tools:

| Command | Description |
|---|---|
| `vdb-sql` | Query the local database dump |
| `vdb-export-dms` | Save your private messages as files |
| `vdb-export-rated-songs` | Export your rated songs as CSV |
| `vdb-notifs-to-songlist` | Turn notifications into a songlist |

Find:

| Command | Description |
|---|---|
| `vdb-find-favourite-albums` | A user's favourite albums |
| `vdb-find-favourite-producers` | A user's favourite producers |
| `vdb-find-favourite-tags` | A user's favourite tags |
| `vdb-find-favourite-vocalists` | A user's favourite vocalists |
| `vdb-rating-diff` | Compare the rated songs of two users |

Graphs:

| Command | Description |
|---|---|
| `vdb-graph-monthly-comments` | Monthly comments on VocaDB |
| `vdb-graph-monthly-edits` | Monthly edits on VocaDB |
| `vdb-graph-monthly-entries` | Monthly entry creations on VocaDB |
| `vdb-graph-monthly-users` | Monthly new users on VocaDB |
| `vdb-graph-rated-songs` | A user's rated songs by month |

Artist tags:

| Command | Description |
|---|---|
| `vdb-artist-tags-by-songs` | Most common tags of an artist's songs |
| `vdb-artist-tags-by-tag` | Most relevant artists for a tag |
| `vdb-artist-tags-verify` | Verify the artists tagged with a tag |

Recommendations:

| Command | Description |
|---|---|
| `vdb-recommend` | Build a recommendation songlist for a user |