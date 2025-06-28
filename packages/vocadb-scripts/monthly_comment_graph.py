"""Generate a monthly comment count graph."""

from vdbpy.api.comments import get_comment_count_before
from vdbpy.utils.graph import get_monthly_graph

get_monthly_graph(get_comment_count_before, "Monthly comments on VocaDB")
