from datetime import datetime

import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

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
    date = datetime.now()
    counts_since_month = []

    while True:
        before_date = f"{date.year}-{date.month}-1"
        monthly_count = count_function(before_date)
        if monthly_count:
            logger.info(f"Before {before_date}: {monthly_count}")
            counts_since_month.append((before_date, monthly_count))
            date -= relativedelta(months=1)
            continue
        break

    counts_by_month = []
    for month_counter in range(len(counts_since_month) - 1):
        month, this_month_amount = counts_since_month[month_counter]
        prev_month_amount = counts_since_month[month_counter + 1][1]
        counts_by_month.append((month, this_month_amount - prev_month_amount))

    logger.info(counts_by_month)
    generate_date_graph(counts_by_month, title=title)
