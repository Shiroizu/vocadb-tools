"""Monthly new user count graph."""

from vdbpy.api.users import get_monthly_user_count

from scripts.graph.graph_utils import build_figure, collect_monthly_data


def _figure():
    data = collect_monthly_data(get_monthly_user_count, "monthly_users")
    return build_figure(data, "Monthly new users on VocaDB", "New users")


def get_monthly_users_png() -> bytes:
    """Return PNG bytes for the monthly new user count graph."""
    return _figure().to_image(format="png")


if __name__ == "__main__":
    _figure().show()
