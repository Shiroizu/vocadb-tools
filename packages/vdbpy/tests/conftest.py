from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture
def yesterday() -> datetime:
    today = datetime.now(UTC)
    return datetime(today.year, today.month, today.day, tzinfo=UTC) - timedelta(days=1)
