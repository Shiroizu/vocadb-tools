Collection of [VocaDB](https://vocadb.net/) related scripts.

Uses [VDBpy](https://github.com/Shiroizu/VDBpy/) under the hood.

Ideas, Pull Requests, etc. are welcome.

## Scripts

### (AT) Artist tag scripts

- Find the most common tags for the artist based on artist's song entries
- Find the most relevant artists for a given tag based on all the tagged songs (slow)
- Verify if tagged artists have tagged songs

### (G) Graph generators

Generate interactive graphs with [Plotly](https://plotly.com/python/) based on monthly counts:

- comments
- edits
- users

Monthly counts are cached indefinitely, which enables quick regeneration.

Generated graphs are displayed in a browser window (localhost).

<img width="472" height="397" alt="Untitled" src="https://github.com/user-attachments/assets/d69a29f4-e889-4a6c-8b6d-b63d69c614c1" />

- rated_songs_by_user generates 2 graphs (monthly publish & rating date), cached for 7 days

### (U) User tools

- Export DMs as markdown files
- Export rated songs entries as csv
- Turn notifications into a songlist

### (US) User statistics

- Find favourite albums
- Find favourite producers
- Find favourite vocalists

## Usage

1) Install [Git](https://git-scm.com/downloads) --> `git clone https://github.com/Shiroizu/VocaDB-scripts` (or download ZIP & extract)

2) `cd VocaDB-scripts`

3) Install [uv](https://docs.astral.sh/uv/)

4) `uv run G_monthly_comments.py`
