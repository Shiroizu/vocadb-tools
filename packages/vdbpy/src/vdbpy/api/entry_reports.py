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
