# ruff: noqa: S101



from vdbpy.types.shared import UserEdit
from vdbpy.utils.data import (
    add_s,
    to_camel_case,
    user_edit_from_dict,
)


def test_to_camel_case() -> None:
    assert to_camel_case("song_types") == "songTypes"
    assert to_camel_case("max_results") == "maxResults"
    assert to_camel_case("single") == "single"


def test_add_s() -> None:
    assert add_s("Song") == "Songs"
    assert add_s("Artist") == "Artists"
    assert add_s("songs") == "songs"


def test_user_edit_from_dict() -> None:
    data = {
        "user_id": 100,
        "edit_date": "2025-09-29T04:32:04.89+00:00",
        "entry_type": "Song",
        "entry_id": 1501,
        "version_id": 12345,
        "edit_event": "Created",
        "changed_fields": ["Names"],
        "update_notes": "",
    }
    edit = user_edit_from_dict(data)
    assert isinstance(edit, UserEdit)
    assert edit.user_id == 100
    assert edit.entry_type == "Song"
    assert edit.entry_id == 1501
    assert edit.version_id == 12345
    assert edit.edit_event == "Created"
    assert edit.changed_fields == ["Names"]
