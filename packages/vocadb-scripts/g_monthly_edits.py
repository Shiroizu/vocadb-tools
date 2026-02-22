"""Generate a monthly edit count graph."""

from vdbpy.api.edits import get_monthly_edit_count
from vdbpy.utils.graph import get_monthly_graph
from vdbpy.utils.logger import get_logger

logger = get_logger("monthly_edits")

get_monthly_graph(get_monthly_edit_count, "Monthly edits on VocaDB")
