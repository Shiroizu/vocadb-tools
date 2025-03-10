"""Generate a monthly comment count graph."""

from api.users import get_user_count
from monthly_graph import get_monthly_graph

get_monthly_graph(get_user_count, "Monthly new users on VocaDB")
