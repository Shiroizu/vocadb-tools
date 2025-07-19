from datetime import datetime

import plotly.graph_objects as go

from vdbpy.utils.logger import get_logger

logger = get_logger("monthly_graph")


def generate_date_graph(
    data: list[tuple[str, int]],
    title="Graph",
    x="Month",
    y="Count",
    date_format="%Y-%m-%d",
):
    dates, values = zip(*data)

    dates = [datetime.strptime(date, date_format) for date in dates]

    sorted_dates_values = sorted(zip(dates, values), key=lambda x: x[0])
    sorted_dates, sorted_values = zip(*sorted_dates_values)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=sorted_dates, y=sorted_values, mode="lines+markers", name="Value")
    )

    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y,
        xaxis={"tickformat": date_format},
    )

    fig.show()


def get_monthly_graph(count_function, title="Graph"):
    """Generate a monthly graph by a given count function."""
    current_date = datetime.now()
    counts_by_month = []
    current_year = current_date.year
    current_month = current_date.month

    while True:
        previous_month = current_month - 1 if current_month > 1 else 12
        previous_month_year = current_year - 1 if current_month == 1 else current_year
        monthly_count = count_function(previous_month_year, previous_month)
        year_month_str = f"{previous_month_year}-{previous_month}"
        if monthly_count:
            logger.info(f"Count for {year_month_str}: {monthly_count}")
            counts_by_month.append((f"{year_month_str}", monthly_count))
            continue
        break

    logger.info(counts_by_month)
    generate_date_graph(counts_by_month, title=title)
