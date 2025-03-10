"""Generate a monthly edit count graph."""

from api.activity import get_edit_count
from monthly_graph import get_monthly_graph

get_monthly_graph(get_edit_count, "Monthly edits on VocaDB")
