"""Shared graph building utilities."""

from collections.abc import Callable
from datetime import UTC, datetime

import plotly.graph_objects as go
from vdbpy.utils.logger import get_logger

logger = get_logger()


def collect_monthly_data(
    count_fn: Callable[[int, int], int], title: str
) -> list[tuple[str, int]]:
    current = datetime.now(UTC)
    year, month = current.year, current.month
    data: list[tuple[str, int]] = []
    while True:
        month = month - 1 if month > 1 else 12
        year = year - 1 if month == 12 else year
        count = count_fn(year, month)
        if not count:
            break
        label = f"{year}-{month:02}"
        logger.info(f"{title}, {label}: {count}")
        data.append((label, count))
    return data


def build_figure(
    data: list[tuple[str, int]],
    title: str,
    y_label: str = "Count",
    trace_name: str = "Value",
) -> go.Figure:
    dates_raw, values = zip(*data, strict=True)
    dates = [datetime.strptime(d, "%Y-%m").replace(tzinfo=UTC) for d in dates_raw]
    sorted_pairs = sorted(zip(dates, values, strict=True), key=lambda x: x[0])
    sorted_dates, sorted_values = zip(*sorted_pairs, strict=True)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sorted_dates, y=sorted_values, mode="lines+markers", name=trace_name
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title=y_label,
        xaxis={"tickformat": "%Y-%m"},
    )
    return fig
