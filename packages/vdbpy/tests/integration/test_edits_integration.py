# ruff: noqa: S101

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from vdbpy.api.edits import (
    get_edits_by_day,
    get_edits_by_entry,
    get_edits_by_month,
    get_edits_until_day,
)

if TYPE_CHECKING:
    from vdbpy.types.shared import VersionTuple

EDITS_SAVE_DIR = Path("edits_by_date")

@pytest.mark.integration
def test_future_edit() -> None:
    edits, _ = get_edits_by_day(2100, 11, 11, limit=None, save_dir=EDITS_SAVE_DIR)
    assert len(edits) == 0


@pytest.mark.integration
def test_last_10_yesterday_edits_with_no_save_dir(yesterday: datetime) -> None:
    ten_edits, limit_reached = get_edits_by_day(
        yesterday.year,
        yesterday.month,
        yesterday.day,
        limit=10,
        save_dir=None,
    )
    assert 1 < len(ten_edits) <= 10
    assert limit_reached


@pytest.mark.integration
def test_yesterday_edits_with_datetime_limit(yesterday: datetime) -> None:
    all_edits, limit_reached = get_edits_by_day(
        yesterday.year,
        yesterday.month,
        yesterday.day,
        limit=yesterday + timedelta(hours=23),
        save_dir=EDITS_SAVE_DIR,
    )
    assert limit_reached
    assert len(all_edits) > 10
    for edit in all_edits:
        assert edit.edit_date > yesterday + timedelta(hours=23)


@pytest.mark.integration
def test_yesterday_edits_with_found_datetime_limit(yesterday: datetime) -> None:
    all_edits, _ = get_edits_by_day(
        yesterday.year,
        yesterday.month,
        yesterday.day,
        limit=yesterday + timedelta(hours=23),
        save_dir=EDITS_SAVE_DIR,
    )
    mid_index = len(all_edits) // 2
    cutoff = all_edits[mid_index].edit_date
    limited_edits, limit_reached = get_edits_by_day(
        yesterday.year,
        yesterday.month,
        yesterday.day,
        limit=cutoff,
        save_dir=EDITS_SAVE_DIR,
    )
    assert len(limited_edits) < len(all_edits)
    assert limit_reached


@pytest.mark.integration
def test_get_edits_by_month_limit_1() -> None:
    today = datetime.now(UTC)
    edits, limit_reached = get_edits_by_month(
        today.year,
        today.month,
        save_dir=EDITS_SAVE_DIR,
        limit=1,
    )
    assert len(edits) == 1
    assert limit_reached


@pytest.mark.integration
def test_get_edits_by_month_limit_2() -> None:
    today = datetime.now(UTC)
    last_month = today.month - 1 if today.month > 1 else 12
    last_year = today.year - 1 if last_month == 12 else today.year
    edits, limit_reached = get_edits_by_month(
        last_year,
        last_month,
        save_dir=EDITS_SAVE_DIR,
        limit=2,
    )
    assert len(edits) == 2
    assert limit_reached
    edit_to_stop: VersionTuple = (
        edits[1].entry_type,
        edits[1].entry_id,
        edits[1].version_id,
    )
    edits2, limit_reached2 = get_edits_by_month(
        last_year,
        last_month,
        save_dir=EDITS_SAVE_DIR,
        limit=edit_to_stop,
    )
    assert len(edits2) == 1
    assert limit_reached2


@pytest.mark.integration
def test_get_edits_until_day() -> None:
    today = datetime.now(UTC)
    start_of_today = datetime(today.year, today.month, today.day, tzinfo=UTC)
    edits = get_edits_until_day(start_of_today, save_dir=EDITS_SAVE_DIR)
    assert len(edits) > 0
    for edit in edits:
        assert edit.edit_date > start_of_today


@pytest.mark.integration
def test_get_edits_until_day_with_version_tuple_limit() -> None:
    today = datetime.now(UTC)
    start_of_today = datetime(today.year, today.month, today.day, tzinfo=UTC)
    edits = get_edits_until_day(start_of_today, save_dir=EDITS_SAVE_DIR, limit=2)
    assert len(edits) == 2
    limit: VersionTuple = (
        edits[1].entry_type,
        edits[1].entry_id,
        edits[1].version_id,
    )
    limited_edits = get_edits_until_day(
        start_of_today, save_dir=EDITS_SAVE_DIR, limit=limit
    )
    assert 1 <= len(limited_edits) <= 10


@pytest.mark.integration
def test_get_edits_by_entry() -> None:
    edits = get_edits_by_entry("Song", 1501, include_deleted=True)
    assert len(edits) >= 1
    assert edits[0].entry_type == "Song"
    assert edits[0].entry_id == 1501
