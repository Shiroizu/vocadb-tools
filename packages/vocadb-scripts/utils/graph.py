from datetime import datetime

import plotly.graph_objects as go


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
