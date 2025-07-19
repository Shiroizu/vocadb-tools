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

- rated_songs_by_user generates 2 graphs (monthly publish & rating date), cached for 7 days

Generated graph is displayed in a browser window (localhost).

Monthly counts are cached indefinitely, which enables quick regeneration.

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

4) `uv run calculate_artist_tags_based_on_songs.py 2595`
