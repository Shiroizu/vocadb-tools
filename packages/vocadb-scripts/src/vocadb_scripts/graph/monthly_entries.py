"""Monthly entry creation graph."""

from vdbpy.config import ACTIVITY_API_URL
from vdbpy.utils.data import get_monthly_count

from scripts.graph.graph_utils import build_figure, collect_monthly_data


def _count_fn(year: int, month: int) -> int:
    return get_monthly_count(year, month, ACTIVITY_API_URL)


def _figure():
    data = collect_monthly_data(_count_fn, "monthly_entries")
    return build_figure(data, "Monthly entry creations on VocaDB", "Entries")


def get_monthly_entries_png() -> bytes:
    """Return PNG bytes for the monthly entry creation graph."""
    return _figure().to_image(format="png")


if __name__ == "__main__":
    _figure().show()
