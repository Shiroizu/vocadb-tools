"""Two plain-text table renderers.

- ``github_table`` wraps ``tabulate`` for markdown-style tables of dict/tuple rows.
- ``aligned_table_lines`` is a dependency-light ``a | b`` renderer with per-column
  truncation, used for SQL results where cell widths are unbounded.

Both measure display width with ``wcwidth`` so CJK names line up in a terminal.
"""

from collections.abc import Iterable, Sequence
from typing import Any

import tabulate as tabulate_module
from tabulate import tabulate
from wcwidth import wcswidth

tabulate_module.WIDE_CHARS_MODE = True


def display_width(text: str) -> int:
    width = wcswidth(text)
    return width if width >= 0 else len(text)


def truncate(text: str, width: int) -> str:
    if display_width(text) <= width:
        return text
    result = ""
    used = 0
    for char in text:
        char_width = display_width(char)
        if used + char_width > width - 1:
            break
        result += char
        used += char_width
    return result + "…"


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))


def cell(value: object) -> str:
    return "NULL" if value is None else str(value)


def aligned_table_lines(
    columns: Sequence[str],
    rows: Iterable[Sequence[object]],
    *,
    max_col_width: int,
) -> list[str]:
    str_rows = [[cell(value) for value in row] for row in rows]
    widths = [display_width(column) for column in columns]
    for row in str_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], display_width(value))
    widths = [min(width, max_col_width) for width in widths]

    def render(cells: Sequence[str]) -> str:
        return " | ".join(
            pad(truncate(value, widths[index]), widths[index])
            for index, value in enumerate(cells)
        )

    separator = "-+-".join("-" * width for width in widths)
    return [render(columns), separator, *(render(row) for row in str_rows)]


def github_table(
    rows: Iterable[Any],
    headers: str | Sequence[str] = "keys",
    **kwargs: Any,
) -> str:
    """Render ``rows`` as a GitHub-markdown table (``tabulate`` passthrough)."""
    return tabulate(rows, headers=headers, tablefmt="github", **kwargs)
