from typing import Any

import requests

from vdbpy.config import ENTRY_REPORTS_URL
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json

logger = get_logger()


def get_entry_reports(session: requests.Session) -> Any:
    """Get entry reports from the admin API."""
    entry_reports = fetch_json(ENTRY_REPORTS_URL, session=session)
    logger.debug(f"Got reports: {len(entry_reports)}")
    logger.debug(f"First report: {entry_reports[0]}")
    return entry_reports
