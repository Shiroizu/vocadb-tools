"""Entry URL -> a list of diffs."""

from dataclasses import dataclass

import requests

from vdbpy.api.edits import get_edits_by_entry
from vdbpy.api.entries import get_cached_entry_version, get_entry_from_link
from vdbpy.api.users import find_user_by_username_1d, get_cached_username_by_id_1d
from vdbpy.api.version_links import VersionLinkKind, parse_version_page_link
from vdbpy.types.shared import EntryStatus, EntryType, UserEdit
from vdbpy.types.versions import EntryVersion
from vdbpy.utils.logger import get_logger
from vocadb_scripts.versions.diff import diff_states
from vocadb_scripts.versions.model import VersionDiff
from vocadb_scripts.versions.song_fields import DEFAULT_STATUS

logger = get_logger()

SUPPORTED_ENTRY_TYPES: frozenset[EntryType] = frozenset({"Song"})


@dataclass
class _Baseline:
    state: EntryVersion | None = None
    status: EntryStatus | None = None
    version_number: int | None = None


def resolve_target(url: str) -> tuple[EntryType, VersionLinkKind, int]:
    """Resolve any of the entry/version URL shapes."""
    if parsed := parse_version_page_link(url):
        return parsed
    entry_type, entry_id = get_entry_from_link(url)
    return (entry_type, "entry", entry_id)


def _check_supported(entry_type: EntryType) -> None:
    if entry_type not in SUPPORTED_ENTRY_TYPES:
        msg = f"{entry_type} diffs are not supported yet (songs only)."
        raise ValueError(msg)


def _author_name(user_id: int) -> str:
    try:
        return get_cached_username_by_id_1d(user_id)
    except requests.exceptions.HTTPError, KeyError:
        return f"user #{user_id}"


def _get_edits(entry_type: EntryType, entry_id: int) -> list[UserEdit]:
    """Every edit of an entry, oldest first."""
    edits = get_edits_by_entry(entry_type, entry_id, include_deleted=True)
    if not edits:
        msg = (
            f"No version history available for {entry_type} {entry_id}. "
            "Entry missing or hit duplicate version numbers."
        )
        raise ValueError(msg)
    return list(reversed(edits))


def _version_number(edit: UserEdit) -> int:
    if edit.version_number is None:
        msg = f"{edit.entry_type} v{edit.version_id} has no version number."
        raise ValueError(msg)
    return edit.version_number


def _fetch_state(edit: UserEdit) -> EntryVersion | None:
    if edit.hidden:
        return None
    return get_cached_entry_version(edit.entry_type, edit.version_id)


def _diff_for_edit(
    edit: UserEdit,
    baseline: _Baseline,
    state: EntryVersion | None,
    entry_version_count: int,
) -> VersionDiff:
    """Diff one version against the baseline, then advance the baseline."""
    diff = VersionDiff(
        entry_type=edit.entry_type,
        entry_id=edit.entry_id,
        version_id=edit.version_id,
        version_number=_version_number(edit),
        edit_date=edit.edit_date,
        edit_event=edit.edit_event,
        author_id=edit.user_id,
        author_name=_author_name(edit.user_id),
        update_notes=edit.update_notes,
        reported_changed_fields=list(edit.changed_fields),
        data_available=state is not None,
        baseline_version_number=baseline.version_number,
        entry_version_count=entry_version_count,
    )

    if state is None:
        return diff

    diff.status = state.status or DEFAULT_STATUS
    diff.previous_status = baseline.status
    diff.changes = diff_states(baseline.state, state)

    baseline.state = state
    baseline.status = diff.status
    baseline.version_number = diff.version_number
    return diff


def get_entry_history(
    entry_type: EntryType,
    entry_id: int,
    limit: int | None = None,
    user_id: int | None = None,
) -> list[VersionDiff]:
    """Entry diffs, oldest first."""
    _check_supported(entry_type)
    edits = _get_edits(entry_type, entry_id)

    wanted = [
        i for i, edit in enumerate(edits) if user_id is None or edit.user_id == user_id
    ]
    if limit is not None:
        wanted = wanted[-limit:]
    if not wanted:
        return []

    start = max(wanted[0] - 1, 0)
    logger.info(
        f"Diffing {len(edits) - start} version(s) of {entry_type} {entry_id}..."
    )

    baseline = _Baseline()
    shown = set(wanted)
    diffs = [
        (i, _diff_for_edit(edit, baseline, _fetch_state(edit), len(edits)))
        for i, edit in enumerate(edits[start:], start)
    ]
    return [diff for i, diff in diffs if i in shown]


def get_version_diff(entry_type: EntryType, version_id: int) -> VersionDiff:
    """Diff one version against the previous version."""
    _check_supported(entry_type)
    state = get_cached_entry_version(entry_type, version_id)
    if state is None:
        msg = f"Version {version_id} data is not available."
        raise ValueError(msg)

    edits = _get_edits(entry_type, state.entry_id)
    index = next(
        (i for i, edit in enumerate(edits) if edit.version_id == version_id), None
    )
    if index is None:
        msg = f"Version {version_id} is not listed in {entry_type} {state.entry_id}."
        raise ValueError(msg)

    baseline = _Baseline()
    previous = next((edit for edit in reversed(edits[:index]) if not edit.hidden), None)
    if previous is not None:
        previous_state = get_cached_entry_version(entry_type, previous.version_id)
        if previous_state is not None:
            baseline = _Baseline(
                state=previous_state,
                status=previous_state.status or DEFAULT_STATUS,
                version_number=_version_number(previous),
            )

    return _diff_for_edit(edits[index], baseline, state, len(edits))


def get_history_from_url(
    url: str, limit: int | None = None, username: str | None = None
) -> list[VersionDiff]:
    entry_type, kind, target_id = resolve_target(url)
    if kind == "version":
        if limit is not None or username is not None:
            logger.info("--limit and --username are ignored for a version link.")
        return [get_version_diff(entry_type, target_id)]
    user_id = find_user_by_username_1d(username)[1] if username else None
    return get_entry_history(entry_type, target_id, limit=limit, user_id=user_id)
