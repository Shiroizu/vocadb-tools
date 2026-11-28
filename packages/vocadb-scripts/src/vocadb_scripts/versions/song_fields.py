"""Song field specs.

Every field not listed in SONG_FIELDS falls through to the generic differ in diff.py.
"""

from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher, unified_diff
from typing import Any

from vdbpy.api.entries import get_entry_link
from vdbpy.types.mappings import changed_field_for
from vdbpy.types.shared import PV, EntryStatus, ExternalLink
from vdbpy.types.songs import Lyrics
from vdbpy.types.versions import EntryVersion
from vdbpy.utils.data import truncate_string_with_ellipsis
from vocadb_scripts.versions.model import EMPTY_DISPLAY, FieldSpec

DEFAULT_STATUS: EntryStatus = "Draft"

IGNORED_KEYS = frozenset(
    {
        "entry_id",
        "version_id",
        "status",
    }
)

LABELS = {
    "song_type": "Song type",
    "default_name_language": "Original language",
    "length_seconds": "Duration",
    "bpm": "BPM",
    "publish_date": "Publish date",
    "original_version_id": "Original version",
    "description_eng": "Description (en)",
    "external_links": "External links",
    "release_events": "Release events",
    "pvs": "PVs",
}

# Present in the archived XML but stripped from the JSON API
UNAVAILABLE_CHANGED_FIELDS = frozenset({"CultureCodes"})

DESCRIPTION_PREVIEW_LENGTH = 100
FRAGMENT_LENGTH = 60
FRAGMENT_CONTEXT = 8
MAX_FRAGMENTS = 5
LYRICS_SNIPPET_LENGTH = 30
MAX_LYRICS_FRAGMENTS = 3
MIN_LYRICS_SIMILARITY = 0.7
LYRICS_DIFF_CONTEXT = 1


def label_for(field_name: str) -> str:
    return LABELS.get(field_name, field_name.replace("_", " ").capitalize())


def _format_length(value: Any) -> str:
    minutes, seconds = divmod(int(value), 60)
    return f"{minutes}:{seconds:02d}"


def _extract_bpm(state: EntryVersion) -> tuple[int | None, int | None]:
    return (
        getattr(state, "min_milli_bpm", None),
        getattr(state, "max_milli_bpm", None),
    )


def _format_bpm(value: Any) -> str:
    low, high = value
    bpms = [round(milli / 1000, 2) for milli in (low, high) if milli]
    if not bpms:
        return EMPTY_DISPLAY
    if len(bpms) == 1 or bpms[0] == bpms[-1]:
        return f"{bpms[0]:g} BPM"
    return f"{bpms[0]:g}-{bpms[-1]:g} BPM"


def _format_publish_date(value: Any) -> str:
    if value is None:
        return EMPTY_DISPLAY
    if not isinstance(value, datetime):
        return str(value)
    return value.strftime("%Y-%m-%d %H:%M" if value.time() else "%Y-%m-%d")


def _format_original_version(value: Any) -> str:
    return get_entry_link("Song", int(value))


NAME_LANGUAGES = {
    "name_non_english": "Non-English",
    "name_romaji": "Romaji",
    "name_english": "English",
}


def _extract_names(state: EntryVersion) -> dict[str, str]:
    return {
        language: name
        for key, language in NAME_LANGUAGES.items()
        if (name := getattr(state, key, ""))
    }


def _format_names(value: Any) -> str:
    return ", ".join(f"{language}: {name}" for language, name in value.items())


def _names_details(before: dict[str, str], after: dict[str, str]) -> list[str]:
    removed = {lang: name for lang, name in before.items() if after.get(lang) != name}
    added = {lang: name for lang, name in after.items() if before.get(lang) != name}
    lines: list[str] = []
    for old_lang, name in list(removed.items()):
        new_lang = next((lang for lang, n in added.items() if n == name), None)
        if new_lang:
            lines.append(f"{name}: {old_lang} → {new_lang}")
            del removed[old_lang], added[new_lang]
    lines.extend(
        f"{lang}: {removed.pop(lang)} → {added.pop(lang)}"
        for lang in [lang for lang in removed if lang in added]
    )
    lines += [f"- {lang}: {name}" for lang, name in removed.items()]
    lines += [f"+ {lang}: {name}" for lang, name in added.items()]
    return lines


def _removed_added(removed: list[str], added: list[str]) -> list[str]:
    if len(removed) == len(added) == 1:
        return [f"{removed[0]} → {added[0]}"]
    return [f"- {item}" for item in removed] + [f"+ {item}" for item in added]


def _list_details(before: list[Any], after: list[Any]) -> list[str]:
    return _removed_added(
        [str(item) for item in before if item not in after],
        [str(item) for item in after if item not in before],
    )


def _keyed_details[T](
    before: list[T],
    after: list[T],
    key: Callable[[T], Hashable],
    text: Callable[[T], str],
    change: Callable[[T, T], str],
) -> list[str]:
    old = {key(item): item for item in before}
    new = {key(item): item for item in after}
    return _removed_added(
        [text(item) for k, item in old.items() if k not in new],
        [text(item) for k, item in new.items() if k not in old],
    ) + [change(old[k], new[k]) for k in old if k in new and old[k] != new[k]]


@dataclass(frozen=True)
class _Artist:
    key: str  # artist ID, or the name for custom artists without an entry
    roles: tuple[str, ...]
    support: bool
    name: str = field(compare=False)

    @property
    def attrs(self) -> str:
        roles = [role for role in self.roles if role != "Default"]
        return ", ".join([*roles, "support"] if self.support else roles)

    @property
    def text(self) -> str:
        return f"{self.name} ({self.attrs})" if self.attrs else self.name


def _extract_artists(state: EntryVersion) -> list[_Artist]:
    artists = [
        _Artist(
            key=f"Ar/{artist.artist_id}" if artist.artist_id else artist.name_hint,
            roles=tuple(sorted(artist.roles)),
            support=artist.is_supporting,
            name=" ".join(
                part
                for part in (
                    artist.name_hint,
                    f"#{artist.artist_id}" if artist.artist_id else "",
                )
                if part
            ),
        )
        for artist in getattr(state, "artists", [])
    ]
    return sorted(artists, key=lambda artist: artist.key)


def _format_artists(value: list[_Artist]) -> str:
    return ", ".join(artist.text for artist in value)


def _artists_details(before: list[_Artist], after: list[_Artist]) -> list[str]:
    return _keyed_details(
        before,
        after,
        key=lambda artist: artist.key,
        text=lambda artist: artist.text,
        change=lambda old, new: (
            f"{new.name} ({old.attrs or 'Default'} → {new.attrs or 'Default'})"
        ),
    )


def _attr_changes(
    old: Any, new: Any, attrs: tuple[tuple[str, str, Callable[[Any], str]], ...]
) -> list[str]:
    """'label: old → new' for each differing attribute."""
    return [
        f"{label}: {show(getattr(old, attr))} → {show(getattr(new, attr))}"
        for attr, label, show in attrs
        if getattr(old, attr) != getattr(new, attr)
    ]


def _flagged(label: str, flags: list[str]) -> str:
    return f"{label} ({', '.join(flags)})" if flags else label


def _disabled_change(old: PV | ExternalLink, new: PV | ExternalLink) -> list[str]:
    if old.disabled == new.disabled:
        return []
    return ["disabled" if new.disabled else "re-enabled"]


def _pv_key(pv: PV) -> tuple[str, str]:
    return (pv.pv_service, pv.pv_id)


def _pv_text(pv: PV) -> str:
    flags = [pv.pv_type] if pv.pv_type != "Original" else []
    flags += ["disabled"] if pv.disabled else []
    return _flagged(f"{pv.pv_service} {pv.pv_id}", flags)


_PV_ATTRS: tuple[tuple[str, str, Callable[[Any], str]], ...] = (
    ("pv_type", "type", str),
    ("name", "title", str),
    ("author", "author", str),
    ("length", "length", _format_length),
    ("publish_date", "date", _format_publish_date),
)


def _pv_change(old: PV, new: PV) -> str:
    parts = _attr_changes(old, new, _PV_ATTRS) + _disabled_change(old, new)
    return _flagged(f"{new.pv_service} {new.pv_id}", parts)


def _format_pvs(value: list[PV]) -> str:
    return ", ".join(_pv_text(pv) for pv in value)


def _pvs_details(before: list[PV], after: list[PV]) -> list[str]:
    return _keyed_details(before, after, key=_pv_key, text=_pv_text, change=_pv_change)


@dataclass(frozen=True)
class _Event:
    event_id: int
    name: str = field(compare=False)

    @property
    def text(self) -> str:
        return f"{self.name} #{self.event_id}" if self.name else f"#{self.event_id}"


def _extract_events(state: EntryVersion) -> list[_Event]:
    events: dict[int, str] = getattr(state, "release_events", {})
    return [_Event(event_id, name) for event_id, name in events.items()]


def _format_events(value: list[_Event]) -> str:
    return ", ".join(event.text for event in value)


def _events_details(before: list[_Event], after: list[_Event]) -> list[str]:
    return _keyed_details(
        before,
        after,
        key=lambda event: event.event_id,
        text=lambda event: event.text,
        change=lambda _old, new: new.text,
    )


# ---- External links (matched by URL, order kept) ---- #

_LINK_ATTRS: tuple[tuple[str, str, Callable[[Any], str]], ...] = (
    ("category", "category", str),
    ("description", "description", lambda value: f'"{value}"' if value else "-"),
)


def _link_text(link: ExternalLink) -> str:
    flags: list[str] = [link.category]
    flags += [f'"{link.description}"'] if link.description else []
    flags += ["disabled"] if link.disabled else []
    return _flagged(link.url, flags)


def _link_change(old: ExternalLink, new: ExternalLink) -> str:
    parts = _attr_changes(old, new, _LINK_ATTRS) + _disabled_change(old, new)
    return _flagged(new.url, parts)


def _format_links(value: list[ExternalLink]) -> str:
    return ", ".join(_link_text(link) for link in value)


def _links_details(before: list[ExternalLink], after: list[ExternalLink]) -> list[str]:
    return _keyed_details(
        before, after, key=lambda link: link.url, text=_link_text, change=_link_change
    )


# ---- Lyrics (matched by lyrics ID. Small text edits shown, else line counts) ---- #

_LYRICS_ATTRS: tuple[tuple[str, str, Callable[[Any], str]], ...] = (
    ("translation_type", "type", str),
    ("language_codes", "languages", lambda codes: ", ".join(codes) or "-"),
    ("source", "source", lambda value: value or "-"),
    ("url", "url", lambda value: value or "-"),
)


def _lyrics_label(lyrics: Lyrics) -> str:
    return _flagged(lyrics.translation_type, list(lyrics.language_codes))


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _lyrics_text(lyrics: Lyrics) -> str:
    lines = [line.strip() for line in lyrics.value.splitlines() if line.strip()]
    text = f"{_lyrics_label(lyrics)} {_plural(len(lines), 'line')}"
    if not lines:
        return text
    snippet = truncate_string_with_ellipsis(lines[0], LYRICS_SNIPPET_LENGTH, "…")
    return f'{text} "{snippet}"'


def _line_counts(old: str, new: str) -> str:
    matcher = SequenceMatcher(a=old.splitlines(), b=new.splitlines(), autojunk=False)
    opcodes = [op for op in matcher.get_opcodes() if op[0] != "equal"]
    added = sum(j2 - j1 for _, _, _, j1, j2 in opcodes)
    removed = sum(i2 - i1 for _, i1, i2, _, _ in opcodes)
    return f"lines +{added} -{removed}"


def _small_edit_fragments(old: str, new: str) -> list[str] | None:
    """Word fragments for a small edit; None for a rewrite."""
    fragments = _word_fragments(old, new)
    similarity = SequenceMatcher(a=old, b=new, autojunk=False).ratio()
    if len(fragments) <= MAX_LYRICS_FRAGMENTS and similarity >= MIN_LYRICS_SIMILARITY:
        return fragments
    return None


def _lyrics_change(old: Lyrics, new: Lyrics) -> str:
    parts = _attr_changes(old, new, _LYRICS_ATTRS)
    if old.value != new.value:
        fragments = _small_edit_fragments(old.value, new.value)
        parts += fragments or [_line_counts(old.value, new.value)]
    return _flagged(_lyrics_label(old), parts)


def _line_diff(old: str, new: str) -> str:
    """Unified line diff without the ---/+++ file headers."""
    lines = unified_diff(
        old.splitlines(), new.splitlines(), n=LYRICS_DIFF_CONTEXT, lineterm=""
    )
    return "\n".join(list(lines)[2:])


def _lyrics_full_diffs(
    before: list[Lyrics], after: list[Lyrics]
) -> list[tuple[str, str]]:
    """Line diffs for rewrites that the summary only counts."""
    old = {lyrics.lyrics_id: lyrics for lyrics in before}
    pairs = [(old[new.lyrics_id], new) for new in after if new.lyrics_id in old]
    return [
        (_lyrics_label(new), diff)
        for prev, new in pairs
        if prev.value != new.value
        and _small_edit_fragments(prev.value, new.value) is None
        and (diff := _line_diff(prev.value, new.value))
    ]


def _format_lyrics(value: list[Lyrics]) -> str:
    return ", ".join(_lyrics_text(lyrics) for lyrics in value)


def _lyrics_details(before: list[Lyrics], after: list[Lyrics]) -> list[str]:
    return _keyed_details(
        before,
        after,
        key=lambda lyrics: lyrics.lyrics_id,
        text=_lyrics_text,
        change=_lyrics_change,
    )


# ---- Free text: descriptions, lyrics (word-level fragments) ---- #


def _quote(text: str) -> str:
    return f'"{truncate_string_with_ellipsis(text, FRAGMENT_LENGTH, ending="…")}"'


def _trim_common(old: str, new: str) -> tuple[str, str]:
    """Cut the shared start/end down to a little context (for unspaced text)."""
    prefix = 0
    while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
        prefix += 1
    suffix = 0
    while (
        suffix < min(len(old), len(new)) - prefix
        and old[-1 - suffix] == new[-1 - suffix]
    ):
        suffix += 1
    start = max(prefix - FRAGMENT_CONTEXT, 0)
    old_end, new_end = len(old) - suffix, len(new) - suffix
    stop = min(suffix, FRAGMENT_CONTEXT)
    head = "…" if start else ""
    tail = "…" if suffix > stop else ""
    return (
        head + old[start : old_end + stop] + tail,
        head + new[start : new_end + stop] + tail,
    )


def _word_fragments(before: str, after: str) -> list[str]:
    old, new = before.split(), after.split()
    fragments: list[str] = []
    matcher = SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_text, new_text = " ".join(old[i1:i2]), " ".join(new[j1:j2])
        if tag == "replace":
            old_text, new_text = _trim_common(old_text, new_text)
            fragments.append(f"{_quote(old_text)} → {_quote(new_text)}")
        elif tag == "delete":
            fragments.append(f"- {_quote(old_text)}")
        elif tag == "insert":
            fragments.append(f"+ {_quote(new_text)}")
    return fragments or ["whitespace only"]


def _format_description(value: Any) -> str:
    text = " ".join(str(value).split())
    return truncate_string_with_ellipsis(text, DESCRIPTION_PREVIEW_LENGTH, ending="…")


def _description_details(before: str, after: str) -> list[str]:
    fragments = _word_fragments(before, after)
    if len(fragments) > MAX_FRAGMENTS:
        extra = len(fragments) - MAX_FRAGMENTS
        fragments = [*fragments[:MAX_FRAGMENTS], f"… {extra} more"]
    return fragments


def _spec(key: str, **kwargs: Any) -> FieldSpec:
    """Build a spec, taking the label and changedFields name from the mappings."""
    return FieldSpec(
        key=key,
        label=label_for(key),
        changed_field=changed_field_for(key, "Song"),
        **kwargs,
    )


SONG_FIELDS: tuple[FieldSpec, ...] = (
    _spec("song_type", empty="Unspecified"),
    _spec("default_name_language", empty="Unspecified"),
    _spec(
        "names",
        empty={},
        extract=_extract_names,
        render=_format_names,
        details=_names_details,
        source_keys=tuple(NAME_LANGUAGES),
    ),
    _spec("aliases", empty=[], render=", ".join, details=_list_details),
    _spec(
        "artists",
        empty=[],
        extract=_extract_artists,
        render=_format_artists,
        details=_artists_details,
    ),
    _spec(
        "pvs",
        empty=[],
        render=_format_pvs,
        details=_pvs_details,
    ),
    _spec(
        "release_events",
        empty=[],
        extract=_extract_events,
        render=_format_events,
        details=_events_details,
    ),
    _spec(
        "external_links",
        empty=[],
        render=_format_links,
        details=_links_details,
    ),
    _spec(
        "lyrics",
        empty=[],
        render=_format_lyrics,
        details=_lyrics_details,
        full_diff=_lyrics_full_diffs,
    ),
    _spec(
        "description",
        render=_format_description,
        details=_description_details,
    ),
    _spec(
        "description_eng",
        render=_format_description,
        details=_description_details,
    ),
    _spec("length_seconds", empty=0, render=_format_length),
    _spec(
        "bpm",
        empty=(None, None),
        extract=_extract_bpm,
        render=_format_bpm,
        source_keys=("min_milli_bpm", "max_milli_bpm"),
    ),
    _spec("publish_date", empty=None, render=_format_publish_date),
    _spec("original_version_id", empty=0, render=_format_original_version),
)
