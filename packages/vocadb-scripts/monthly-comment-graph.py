"""Generate a monthly comment count graph."""

from datetime import datetime

from dateutil.relativedelta import relativedelta

from api.comments import get_comment_count
from utils.graph import generate_date_graph

date = datetime.now()
comments_since_month = []

while True:
    before_date = f"{date.year}-{date.month}-1"
    comment_count = get_comment_count(before_date)
    if comment_count:
        print(f"Before {before_date}: {comment_count}")
        comments_since_month.append((before_date, comment_count))
        date -= relativedelta(months=1)
        continue
    break

comments_by_month = []
for month_counter in range(len(comments_since_month) - 1):
    month, this_month_amount = comments_since_month[month_counter]
    prev_month_amount = comments_since_month[month_counter + 1][1]
    comments_by_month.append((month, this_month_amount - prev_month_amount))

print(comments_by_month)
generate_date_graph(comments_by_month, title="Monthly comments on VocaDB")
