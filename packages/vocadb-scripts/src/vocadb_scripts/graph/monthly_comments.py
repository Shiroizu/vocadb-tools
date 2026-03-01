"""Monthly comment count graph."""

from vdbpy.api.comments import get_monthly_comment_count

from scripts.graph.graph_utils import build_figure, collect_monthly_data


def _figure():
    data = collect_monthly_data(get_monthly_comment_count, "monthly_comments")
    return build_figure(data, "Monthly comments on VocaDB", "Comments")


def get_monthly_comments_png() -> bytes:
    """Return PNG bytes for the monthly comment count graph."""
    return _figure().to_image(format="png")


if __name__ == "__main__":
    _figure().show()
