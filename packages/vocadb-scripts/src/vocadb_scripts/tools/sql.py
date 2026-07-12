"""Run a read-only SELECT against the preprocessed VocaDB dump database.

The first query is slow and later ones are instant.

Usage:

    uv run scripts/tools/sql.py --schema
    uv run scripts/tools/sql.py "SELECT id, song_type FROM songs LIMIT 5"
    uv run scripts/tools/sql.py --max-rows 20 "SELECT tag_id FROM entry_tags"

Note that you can also use a visual database browsing tool.
"""

from __future__ import annotations

import argparse

from vdbpy.utils.dump_sql import DumpDB, SqlError, SqlResult
from vdbpy.utils.logger import get_logger
from wcwidth import wcswidth

logger = get_logger()

MAX_COL_WIDTH = 40
DEFAULT_MAX_ROWS = 100


def _display_width(text: str) -> int:
    width = wcswidth(text)
    return width if width >= 0 else len(text)


def _truncate(text: str, width: int) -> str:
    if _display_width(text) <= width:
        return text
    result = ""
    used = 0
    for char in text:
        char_width = _display_width(char)
        if used + char_width > width - 1:
            break
        result += char
        used += char_width
    return result + "…"


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def _cell(value: object) -> str:
    return "NULL" if value is None else str(value)


def format_result(result: SqlResult) -> str:
    """Render a query result as an aligned monospace table."""
    if not result.columns:
        return "Query returned no columns."
    if not result.rows:
        return "Query returned no rows."

    str_rows = [[_cell(value) for value in row] for row in result.rows]
    widths = [_display_width(column) for column in result.columns]
    for row in str_rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], _display_width(cell))
    widths = [min(width, MAX_COL_WIDTH) for width in widths]

    def render(cells: list[str]) -> str:
        return " | ".join(
            _pad(_truncate(cell, widths[index]), widths[index])
            for index, cell in enumerate(cells)
        )

    separator = "-+-".join("-" * width for width in widths)
    lines = [render(result.columns), separator, *(render(row) for row in str_rows)]
    if result.truncated:
        lines.extend(("", f"(showing the first {len(str_rows)} rows; more matched)"))
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


if __name__ == "__main__":
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
