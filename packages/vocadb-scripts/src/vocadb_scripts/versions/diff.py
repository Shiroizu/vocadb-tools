"""Two version states -> list[FieldChange]."""

from collections.abc import Callable
from dataclasses import fields
from typing import Any

from vdbpy.types.mappings import changed_field_for
from vdbpy.types.versions import EntryVersion
from vdbpy.utils.data import truncate_string_with_ellipsis
from vocadb_scripts.versions.model import FieldChange, FieldSpec, Verb
from vocadb_scripts.versions.song_fields import (
    IGNORED_KEYS,
    SONG_FIELDS,
    label_for,
)

FALLBACK_PREVIEW_LENGTH = 100


def _verb(*, was_empty: bool, is_empty: bool) -> Verb:
    if was_empty:
        return "added"
    if is_empty:
        return "removed"
    return "updated"


def diff_field(
    spec: FieldSpec,
    before_state: EntryVersion | None,
    after_state: EntryVersion | None,
    *,
    specced: bool = True,
) -> FieldChange | None:
    before = spec.get(before_state)
    after = spec.get(after_state)
    if before == after:
        return None

    verb = _verb(was_empty=spec.is_empty(before), is_empty=spec.is_empty(after))

    details: list[str] = []
    full_diffs: list[tuple[str, str]] = []
    if verb == "updated" and spec.details:
        details = spec.details(before, after)
        verb = "updated" if details else "reordered"
    if verb == "updated" and spec.full_diff:
        full_diffs = spec.full_diff(before, after)

    return FieldChange(
        key=spec.key,
        label=spec.label,
        verb=verb,
        before=spec.show(before),
        after=spec.show(after),
        changed_field=spec.changed_field,
        specced=specced,
        details=details,
        full_diffs=full_diffs,
    )


def _preview(value: Any) -> str:
    if isinstance(value, list):
        return f"{len(value)} item(s)"
    return truncate_string_with_ellipsis(
        " ".join(str(value).split()), FALLBACK_PREVIEW_LENGTH, ending="…"
    )


def _extract_blank_as_none(key: str) -> Callable[[EntryVersion], Any]:
    def extract(state: EntryVersion) -> Any:
        value = getattr(state, key, None)
        return None if value in ("", [], {}) else value

    return extract


def _fallback_spec(key: str) -> FieldSpec:
    return FieldSpec(
        key=key,
        label=label_for(key),
        changed_field=changed_field_for(key, "Song"),
        empty=None,
        extract=_extract_blank_as_none(key),
        render=_preview,
    )


def _state_field_names(state: EntryVersion | None) -> frozenset[str]:
    return frozenset(f.name for f in fields(state)) if state else frozenset()


def _claimed_keys(specs: tuple[FieldSpec, ...]) -> frozenset[str]:
    return frozenset(key for spec in specs for key in spec.claimed_keys())


def diff_states(
    before_state: EntryVersion | None,
    after_state: EntryVersion | None,
    specs: tuple[FieldSpec, ...] = SONG_FIELDS,
) -> list[FieldChange]:
    """Diff two reconstructed version states."""
    seen_keys = _state_field_names(before_state) | _state_field_names(after_state)
    unspecced = sorted(seen_keys - _claimed_keys(specs) - IGNORED_KEYS)
    candidates = [(spec, True) for spec in specs]
    candidates += [(_fallback_spec(key), False) for key in unspecced]

    changes = (
        diff_field(spec, before_state, after_state, specced=specced)
        for spec, specced in candidates
    )
    return [change for change in changes if change]
