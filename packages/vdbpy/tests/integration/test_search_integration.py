# ruff: noqa: S101

from typing import get_args

import pytest

from vdbpy.api.search import search_entries
from vdbpy.types.shared import EntryType


@pytest.mark.integration
@pytest.mark.parametrize("entry_type", get_args(EntryType))
def test_search_all_entry_types(entry_type: EntryType) -> None:
    results, total_count = search_entries("Test", entry_type, max_results=1)
    assert len(results) == 1
    assert total_count >= 1
