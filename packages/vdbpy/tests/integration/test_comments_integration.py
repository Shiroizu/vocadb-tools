# ruff: noqa: S101

from datetime import UTC, datetime, timedelta

import pytest

from vdbpy.api.comments import get_comments_since


@pytest.mark.integration
def test_get_comments_since() -> None:
    since = datetime.now(UTC) - timedelta(hours=1)
    result = get_comments_since(since)
    assert "items" in result
    assert isinstance(result["items"], list)
