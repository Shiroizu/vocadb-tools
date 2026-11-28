"""Render entry diffs."""

from vdbpy.api.entries import get_entry_link
from vdbpy.api.version_links import get_version_link
from vdbpy.utils.tables import display_width, pad
from vocadb_scripts.versions.model import VersionDiff
from vocadb_scripts.versions.song_fields import UNAVAILABLE_CHANGED_FIELDS

VERB_MARKERS = {
    "added": "+",
    "updated": "~",
    "removed": "-",
    "reordered": "⇅",
}

PENDING_NOTE = "(field-level diff pending)"
FULL_DIFF_NOTE = "(full diff below)"


def _status(diff: VersionDiff) -> str:
    """Only on creation or when it changed."""
    if diff.status_changed:
        return f"{diff.previous_status} → {diff.status}  "
    if diff.is_creation and diff.status:
        return f"{diff.status}  "
    return ""


def _header(diff: VersionDiff) -> str:
    when = diff.edit_date.strftime("%Y-%m-%d %H:%M")
    version = f"v{diff.version_number}"
    return (
        f"{pad(version, 4)} {when}  {pad(diff.edit_event, 8)}  "
        f"{_status(diff)}by {diff.author_name}"
    )


def _stale_baseline_line(diff: VersionDiff) -> str:
    baseline = diff.baseline_version_number
    first_hidden = 0 if baseline is None else baseline + 1
    last_hidden = diff.version_number - 1
    hidden = (
        f"v{first_hidden}"
        if first_hidden == last_hidden
        else f"v{first_hidden}-v{last_hidden}"
    )
    compared_to = "an empty entry" if baseline is None else f"v{baseline}"
    return (
        f"    ! Compared against {compared_to}; {hidden} hidden, "
        "so those changes are included below"
    )


def _change_lines(
    diff: VersionDiff, label_width: int, *, inline_full_diffs: bool
) -> list[str]:
    lines: list[str] = []
    for change in diff.changes:
        marker = VERB_MARKERS[change.verb]
        label = pad(change.label, label_width)
        if change.details:
            value = ", ".join(change.details)
        elif change.verb == "added":
            value = change.after
        elif change.verb == "removed":
            value = change.before
        else:
            value = f"{change.before} → {change.after}"
        suffix = "" if change.specced else f"   {PENDING_NOTE}"
        if change.full_diffs and not inline_full_diffs:
            suffix += f"   {FULL_DIFF_NOTE}"
        lines.append(f"    {marker} {label}  {value}{suffix}")
        if inline_full_diffs:
            for title, body in change.full_diffs:
                lines.append(f"      {title}")
                lines.extend(f"      {line}" for line in body.splitlines())
    return lines


def _verification_lines(diff: VersionDiff) -> list[str]:
    detected = diff.detected_changed_fields
    reported = set(diff.reported_changed_fields)
    lines: list[str] = [
        f"    ! VocaDB reports '{missing}' changed, comparison detected nothing"
        for missing in sorted(reported - detected - UNAVAILABLE_CHANGED_FIELDS)
    ]
    lines.extend(
        f"    ! '{unavailable}' is not exposed by the versions API"
        for unavailable in sorted(reported & UNAVAILABLE_CHANGED_FIELDS)
    )
    if not diff.is_creation and not diff.baseline_is_stale:
        lines.extend(
            f"    ! Detected '{extra}' changed, VocaDB did not report it"
            for extra in sorted(detected - reported)
        )
    return lines


def render_full_diffs(diffs: list[VersionDiff]) -> str:
    """All full diffs, unindented so `diff` highlighting applies."""
    return "\n\n".join(
        f"v{diff.version_number} {title}\n{body}"
        for diff in diffs
        for change in diff.changes
        for title, body in change.full_diffs
    )


def render_history(
    diffs: list[VersionDiff],
    *,
    verify: bool = False,
    inline_full_diffs: bool = True,
) -> str:
    """Full diffs are indented under their change, or noted for render_full_diffs."""
    if not diffs:
        return "No revisions to show."

    first = diffs[0]
    entry_link = get_entry_link(first.entry_type, first.entry_id)
    label_width = max(
        (display_width(change.label) for diff in diffs for change in diff.changes),
        default=0,
    )

    lines = [
        f"{first.entry_type} {first.entry_id} — {len(diffs)} revision(s)",
        entry_link,
        "",
    ]

    for diff in diffs:
        lines.append(_header(diff))
        if version_link := get_version_link(diff.entry_type, diff.version_id):
            lines.append(f"    {version_link}")
        if not diff.data_available:
            lines.extend(["    (version data is moderator-only)", ""])
            continue
        if notes := " ".join(diff.update_notes.split()):
            lines.append(f"    > {notes}")
        if diff.baseline_is_stale:
            lines.append(_stale_baseline_line(diff))
        change_lines = _change_lines(
            diff, label_width, inline_full_diffs=inline_full_diffs
        )
        lines.extend(change_lines or ["    (no content changes)"])
        if verify:
            lines.extend(_verification_lines(diff))
        lines.append("")

    return "\n".join(lines)
