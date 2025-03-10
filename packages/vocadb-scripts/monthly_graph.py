"""Generate a monthly graph by a given count function."""

from datetime import datetime

from dateutil.relativedelta import relativedelta

from utils.graph import generate_date_graph


def get_monthly_graph(count_function, title="Graph"):

    date = datetime.now()
    counts_since_month = []

    while True:
        before_date = f"{date.year}-{date.month}-1"
        monthly_count = count_function(before_date)
        if monthly_count:
            print(f"Before {before_date}: {monthly_count}")
            counts_since_month.append((before_date, monthly_count))
            date -= relativedelta(months=1)
            continue
        break

    counts_by_month = []
    for month_counter in range(len(counts_since_month) - 1):
        month, this_month_amount = counts_since_month[month_counter]
        prev_month_amount = counts_since_month[month_counter + 1][1]
        counts_by_month.append((month, this_month_amount - prev_month_amount))

    print(counts_by_month)
    generate_date_graph(counts_by_month, title=title)
