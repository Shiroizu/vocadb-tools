# The first run downloads dump.zip into the vdbpy cache.

import itertools
from collections import Counter

from vdbpy.utils.dump import Dump
from vdbpy.utils.logger import get_logger

logger = get_logger("DumpExample")


def main() -> None:
    dump = Dump.load()

    logger.info("First 5 artists:")
    for artist in itertools.islice(dump.artists(), 5):
        name = artist.translated_name.english if artist.translated_name else "?"
        logger.info(f"  #{artist.id} {name} ({artist.artist_type})")

    song = next(s for s in dump.songs() if s.tags)
    name = song.translated_name.english if song.translated_name else "?"
    logger.info(f"Top tags on song #{song.id} '{name}':")
    for usage in sorted(song.tags, key=lambda t: t.count, reverse=True)[:5]:
        tag = usage.tag.name_hint if usage.tag else "?"
        logger.info(f"  {tag}: {usage.count}")

    tags = list(dump.tags())
    with_parent = [t for t in tags if t.parent]
    logger.info(f"{len(tags)} tags total, {len(with_parent)} have a parent tag.")

    categories = Counter(t.category_name or "(none)" for t in tags)
    logger.info("Tag categories:")
    for category, count in categories.most_common(10):
        logger.info(f"  {category}: {count}")

    event_count = sum(1 for _ in dump.events())
    series_count = sum(1 for _ in dump.event_series())
    logger.info(f"{event_count} events across {series_count} event series.")


if __name__ == "__main__":
    main()
