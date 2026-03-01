"""Monthly edit count graph."""

from vdbpy.api.edits import get_monthly_edit_count

from scripts.graph.graph_utils import build_figure, collect_monthly_data


def _figure():
    data = collect_monthly_data(get_monthly_edit_count, "monthly_edits")
    return build_figure(data, "Monthly edits on VocaDB", "Edits")


def get_monthly_edits_png() -> bytes:
    """Return PNG bytes for the monthly edit count graph."""
    return _figure().to_image(format="png")


if __name__ == "__main__":
    _figure().show()
