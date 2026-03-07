# ruff: noqa: S101

from datetime import UTC, datetime

import pytest

from vdbpy.api.edits import _filter_edits, _merge_edit_lists, _verify_edits
from vdbpy.types.shared import EntryType, UserEdit


def _edit(
    entry_type: EntryType = "Song",
    entry_id: int = 1,
    version_id: int = 1,
    edit_date: datetime | None = None,
) -> UserEdit:
    return UserEdit(
        user_id=0,
        edit_date=edit_date or datetime(2025, 1, 1, tzinfo=UTC),
        entry_type=entry_type,
        entry_id=entry_id,
        version_id=version_id,
        edit_event="Updated",
        changed_fields=[],
        update_notes="",
    )


def test_verify_edits_empty() -> None:
    _verify_edits([])


def test_verify_edits_single() -> None:
    _verify_edits([_edit(version_id=1)])


def test_verify_edits_sorted_by_date_desc() -> None:
    e1 = _edit(version_id=1, edit_date=datetime(2025, 1, 3, tzinfo=UTC))
    e2 = _edit(version_id=2, edit_date=datetime(2025, 1, 2, tzinfo=UTC))
    e3 = _edit(version_id=3, edit_date=datetime(2025, 1, 1, tzinfo=UTC))
    _verify_edits([e1, e2, e3])


def test_verify_edits_duplicate_raises() -> None:
    e1 = _edit(entry_type="Song", entry_id=1, version_id=1)
    e2 = _edit(entry_type="Song", entry_id=1, version_id=1)
    with pytest.raises(AssertionError, match="Duplicate"):
        _verify_edits([e1, e2])


def test_filter_edits_by_int_limit() -> None:
    edits = [_edit(version_id=i) for i in range(1, 6)]
    result, limit_reached = _filter_edits(edits, 2)
    assert len(result) == 2
    assert limit_reached is True
    assert result[0].version_id == 1
    assert result[1].version_id == 2


def test_filter_edits_by_int_limit_not_reached() -> None:
    edits = [_edit(version_id=1), _edit(version_id=2)]
    result, limit_reached = _filter_edits(edits, 10)
    assert len(result) == 2
    assert limit_reached is False


def test_filter_edits_by_version_tuple() -> None:
    e1 = _edit(entry_type="Song", entry_id=1, version_id=10)
    e2 = _edit(entry_type="Song", entry_id=1, version_id=20)
    e3 = _edit(entry_type="Song", entry_id=1, version_id=30)
    edits = [e1, e2, e3]
    result, limit_reached = _filter_edits(edits, ("Song", 1, 20))
    assert len(result) == 1
    assert result[0].version_id == 10
    assert limit_reached is True


def test_filter_edits_by_datetime() -> None:
    cutoff = datetime(2025, 1, 2, 12, 0, 0, tzinfo=UTC)
    e1 = _edit(version_id=1, edit_date=datetime(2025, 1, 3, tzinfo=UTC))
    e2 = _edit(version_id=2, edit_date=datetime(2025, 1, 2, tzinfo=UTC))
    e3 = _edit(version_id=3, edit_date=datetime(2025, 1, 1, tzinfo=UTC))
    edits = [e1, e2, e3]
    result, limit_reached = _filter_edits(edits, cutoff)
    assert len(result) == 1
    assert result[0].version_id == 1
    assert limit_reached is True


def test_merge_edit_lists_empty_both() -> None:
    result = _merge_edit_lists([], [])
    assert result == []


def test_merge_edit_lists_new_only() -> None:
    e = _edit(version_id=1)
    result = _merge_edit_lists([e], [])
    assert len(result) == 1
    assert result[0].version_id == 1


def test_merge_edit_lists_previous_only() -> None:
    e = _edit(version_id=1)
    result = _merge_edit_lists([], [e])
    assert len(result) == 1


def test_merge_edit_lists_deduplicates() -> None:
    e = _edit(version_id=1)
    result = _merge_edit_lists([e], [e])
    assert len(result) == 1


def test_merge_edit_lists_combines_sorted() -> None:
    e_new = _edit(version_id=1, edit_date=datetime(2025, 1, 2, tzinfo=UTC))
    e_prev = _edit(version_id=2, edit_date=datetime(2025, 1, 1, tzinfo=UTC))
    result = _merge_edit_lists([e_new], [e_prev])
    assert len(result) == 2
    assert result[0].version_id == 1
    assert result[1].version_id == 2
