"""Generate a monthly edit count graph."""

from datetime import datetime

from dateutil.relativedelta import relativedelta

from api.activity import get_edit_count
from utils.graph import generate_date_graph

date = datetime.now()
edit_since_month = []

while True:
    before_date = f"{date.year}-{date.month}-1"
    edit_count = get_edit_count(before_date)
    if edit_count:
        print(f"Before {before_date}: {edit_count}")
        edit_since_month.append((before_date, edit_count))
        date -= relativedelta(months=1)
        continue
    break

edits_by_month = []
for month_counter in range(len(edit_since_month) - 1):
    month, this_month_amount = edit_since_month[month_counter]
    prev_month_amount = edit_since_month[month_counter + 1][1]
    edits_by_month.append((month, this_month_amount - prev_month_amount))

print(edits_by_month)
generate_date_graph(edits_by_month, title="Monthly edits on VocaDB")
