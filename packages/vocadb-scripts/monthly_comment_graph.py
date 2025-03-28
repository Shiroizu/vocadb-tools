"""Generate a monthly comment count graph."""

from api.comments import get_comment_count
from utils.graph import get_monthly_graph

get_monthly_graph(get_comment_count, "Monthly comments on VocaDB")
