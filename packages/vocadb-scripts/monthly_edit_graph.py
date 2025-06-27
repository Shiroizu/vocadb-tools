"""Generate a monthly edit count graph."""

from vdbpy.api.activity import get_edit_count
from vdbpy.utils.graph import get_monthly_graph

get_monthly_graph(get_edit_count, "Monthly edits on VocaDB")
