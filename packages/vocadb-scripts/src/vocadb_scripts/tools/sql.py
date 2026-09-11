"""Run a read-only SELECT against the preprocessed VocaDB dump database.

The first query is slow and later ones are instant.

Usage:

    uv run vdb-sql --schema
    uv run vdb-sql "SELECT id, song_type FROM songs LIMIT 5"
    uv run vdb-sql --max-rows 20 "SELECT tag_id FROM entry_tags"

Note that you can also use a visual database browsing tool.
"""

from __future__ import annotations

import argparse

from vdbpy.utils.dump_sql import DumpDB, SqlError, SqlResult
from vdbpy.utils.logger import get_logger
from vdbpy.utils.tables import aligned_table_lines

logger = get_logger()

MAX_COL_WIDTH = 40
DEFAULT_MAX_ROWS = 100


def format_result(result: SqlResult) -> str:
    """Render a query result as an aligned monospace table."""
    if not result.columns:
        return "Query returned no columns."
    if not result.rows:
        return "Query returned no rows."

    lines = aligned_table_lines(
        result.columns, result.rows, max_col_width=MAX_COL_WIDTH
    )
    if result.truncated:
        lines.extend(("", f"(showing the first {len(result.rows)} rows; more matched)"))
    return "\n".join(lines)


def main(query: str, *, max_rows: int = DEFAULT_MAX_ROWS) -> str:
    db = DumpDB.build()
    result = db.run_readonly_select(query, max_rows=max_rows)
    return format_result(result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a read-only SELECT against the VocaDB dump database.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="A single SELECT (or WITH) statement. See --schema for the tables.",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print the database schema (CREATE statements) and exit.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=DEFAULT_MAX_ROWS,
        help=f"Maximum number of rows to fetch (default: {DEFAULT_MAX_ROWS}).",
    )
    return parser.parse_args()


def cli() -> None:
    logger = get_logger("sql")
    args = parse_args()
    if args.schema:
        logger.info(DumpDB.build().schema_sql())
    elif not args.query:
        raise SystemExit("Provide a SELECT query, or use --schema to see the schema.")
    else:
        try:
            logger.info(main(args.query, max_rows=args.max_rows))
        except SqlError as exc:
            raise SystemExit(f"Query rejected: {exc}") from exc


if __name__ == "__main__":
    cli()
