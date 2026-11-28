"""Display human-readable entry diffs.

Usage:
    vdb-entry-history https://vocadb.net/S/1
    vdb-entry-history https://vocadb.net/Song/Versions/1 --limit 10
    vdb-entry-history https://vocadb.net/Song/ViewVersion/1234 --verify
    vdb-entry-history https://vocadb.net/S/1 --username Shiroizu --limit 5
"""

import argparse

from vdbpy.utils.logger import get_logger
from vocadb_scripts.versions.fetch import get_history_from_url
from vocadb_scripts.versions.render import VERB_MARKERS, render_history

LEGEND = "\n".join(
    [
        "symbols:",
        *(f"  {marker}  {verb}" for verb, marker in VERB_MARKERS.items()),
        "  >  edit notes",
        "  !  warning",
    ]
)


def main(
    url: str,
    limit: int | None = None,
    username: str | None = None,
    *,
    verify: bool = False,
) -> str:
    diffs = get_history_from_url(url, limit=limit, username=username)
    return render_history(diffs, verify=verify)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=LEGEND,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="Entry or version URL, e.g. https://vocadb.net/S/1")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Show only the N most recent revisions",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Show only revisions by this user (combines with --limit)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Cross-check against VocaDB's own changedFields list",
    )
    return parser.parse_args()


def cli() -> None:
    logger = get_logger("entry-history")
    args = parse_args()
    try:
        logger.info(main(args.url, args.limit, args.username, verify=args.verify))
    except ValueError as e:
        raise SystemExit(str(e)) from e


if __name__ == "__main__":
    cli()
