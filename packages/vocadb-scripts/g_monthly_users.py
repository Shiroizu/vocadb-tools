"""Generate a monthly comment count graph."""

from vdbpy.api.users import get_monthly_user_count
from vdbpy.utils.graph import get_monthly_graph
from vdbpy.utils.logger import get_logger

logger = get_logger("monthly_users")

get_monthly_graph(get_monthly_user_count, "Monthly new users on VocaDB")
