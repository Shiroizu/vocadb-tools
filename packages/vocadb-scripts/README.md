Collection of [VocaDB](https://vocadb.net/) related scripts.

Uses [VDBpy](https://github.com/Shiroizu/VDBpy/) under the hood.

Ideas, Pull Requests, etc. are welcome.

## Scripts

### Artist tag scripts

- `at_calculate_artist_tags_based_on_songs.py` Find the most common tags for the artist based on artist's song entries
- `at_calculate_most_relevant_artists_by_a_tag.py` Find the most relevant artists for a given tag based on all the tagged songs (slow)
- `at_verify_tagged_artists.py` Verify if tagged artists have tagged songs

### Graph generators

Generate interactive graphs with [Plotly](https://plotly.com/python/) based on monthly counts:

- `g_monthly_comments.py`
- `g_monthly_edits.py`
- `g_monthly_users.py`

Monthly counts are cached indefinitely, which enables quick regeneration.

Generated graphs are displayed in a browser window (localhost).

- `g_rated_songs_by_user.py` generates 2 graphs (monthly publish & rating date), cached for 7 days

### User tools

- `ut_export_dms.py` Export DMs as markdown files
- `ut_export_rated_song_entries_as_csv.py`
- `ut_notifications_to_songlist.py` Turn song notifications into a songlist

### User statistics

(7d cached data)

- `us_find_favourite_albums.py`
- `us_find_favourite_producers.py`
- `us_find_favourite_vocalists.py`

## Screenshots

<img width="472" height="397" alt="Untitled" src="https://github.com/user-attachments/assets/d69a29f4-e889-4a6c-8b6d-b63d69c614c1" />

## Usage

1) Install [Git](https://git-scm.com/downloads) --> `git clone https://github.com/Shiroizu/VocaDB-scripts` (or download ZIP & extract)

2) `cd VocaDB-scripts`

3) Install [uv](https://docs.astral.sh/uv/)

4) Run commands with "uv run": `uv run g_monthly_comments.py`
