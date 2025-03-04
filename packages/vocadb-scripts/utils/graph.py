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
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, mode="lines+markers", name="Value"))

    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y,
        xaxis={"tickformat": date_format},
    )

    fig.show()
