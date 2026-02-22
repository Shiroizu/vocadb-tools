"""Generate a monthly songs added graph."""

from vdbpy.config import (
    ACTIVITY_API_URL,
)
from vdbpy.types.shared import EntryType
from vdbpy.utils.data import get_monthly_count
from vdbpy.utils.graph import get_monthly_graph
from vdbpy.utils.logger import get_logger

logger = get_logger("monthly_songs_added")

entry_types: list[EntryType] = ["Song", "Album", "Artist"]
for entry_type in entry_types:
    logger.info(f"Counting entry type: {entry_type}")

    def get_created_entry_count_by_month(year: int, month: int) -> int:
        return get_monthly_count(year, month, ACTIVITY_API_URL)

    get_monthly_graph(
        get_created_entry_count_by_month,
        f"Monthly created {entry_type.lower()} entries on VocaDB",
    )
    _ = input("Press enter to continue")
