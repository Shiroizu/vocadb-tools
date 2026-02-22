"""Generate a monthly comment count graph."""

from vdbpy.api.comments import get_monthly_comment_count
from vdbpy.utils.graph import get_monthly_graph
from vdbpy.utils.logger import get_logger

logger = get_logger("monthly_edits")

get_monthly_graph(get_monthly_comment_count, "Monthly comments on VocaDB")
