"""Generate a monthly edit count graph."""

from vdbpy.api.activity import get_edit_count_before
from vdbpy.utils.graph import get_monthly_graph

get_monthly_graph(get_edit_count_before, "Monthly edits on VocaDB")
