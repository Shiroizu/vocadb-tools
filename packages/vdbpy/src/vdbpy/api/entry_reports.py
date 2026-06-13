from typing import Any

import requests

from vdbpy.config import ENTRY_REPORTS_URL
from vdbpy.utils.cache import cache_with_expiration
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_json

logger = get_logger()

OPEN_ENTRY_REPORTS_URL = f"{ENTRY_REPORTS_URL}?status=Open"
CLOSED_ENTRY_REPORTS_URL = f"{ENTRY_REPORTS_URL}?status=Closed"


def get_entry_reports(session: requests.Session) -> Any:
    """Get entry reports from the admin API."""
    entry_reports = fetch_json(ENTRY_REPORTS_URL, session=session)
    logger.debug(f"Got reports: {len(entry_reports)}")
    logger.debug(f"First report: {entry_reports[0]}")
    return entry_reports


def get_open_entry_reports(session: requests.Session) -> Any:
    """Get open entry reports from the admin API."""
    entry_reports = fetch_json(OPEN_ENTRY_REPORTS_URL, session=session)
    logger.debug(f"Got open reports: {len(entry_reports)}")
    if entry_reports:
        logger.debug(f"First open report: {entry_reports[0]}")
    return entry_reports


def get_closed_entry_reports(session: requests.Session) -> Any:
    """Get closed entry reports from the admin API."""
    entry_reports = fetch_json(CLOSED_ENTRY_REPORTS_URL, session=session)
    logger.debug(f"Got closed reports: {len(entry_reports)}")
    return entry_reports


@cache_with_expiration(hours=1)
def get_cached_open_entry_reports_1h(session: requests.Session) -> Any:
    """Get open entry reports, cached for one hour."""
    return get_open_entry_reports(session)


def close_entry_report(session: requests.Session, report_id: int) -> bool:
    """Close an entry report by ID."""
    url = f"{ENTRY_REPORTS_URL}/{report_id}"
    logger.info(f"Closing entry report {report_id} at {url}")
    response = None
    try:
        response = session.delete(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.warning(
            f"Could not close report {report_id}: "
            f"{response.status_code if response is not None else 'no response'} "
            f"{response.text if response is not None else ''}"
        )
        return False
    logger.info(f"Report {report_id} closed.")
    return True
