# ruff: noqa: S101

from datetime import UTC, datetime

from vdbpy.types.songs import SongSearchParams


def test_to_url_params_empty() -> None:
    params = SongSearchParams()
    result = params.to_url_params()
    # With all defaults, only nameMatchMode may appear (default "Auto" is truthy)
    assert "query" not in result
    assert "maxResults" not in result or result["maxResults"] == 0


def test_to_url_params_query_and_max_results() -> None:
    params = SongSearchParams(query="hello", max_results=5)
    result = params.to_url_params()
    assert result["query"] == "hello"
    assert result["maxResults"] == 5


def test_to_url_params_song_types_set() -> None:
    params = SongSearchParams(song_types={"Original", "Cover"}, max_results=1)
    result = params.to_url_params()
    assert "songTypes" in result
    assert (
        result["songTypes"] == "Cover,Original"
        or result["songTypes"] == "Original,Cover"
    )


def test_to_url_params_tag_ids_single() -> None:
    params = SongSearchParams(tag_ids={52}, max_results=1)
    result = params.to_url_params()
    assert "tagId[]" in result
    assert result["tagId[]"] == "52"


def test_to_url_params_tag_ids_multiple() -> None:
    params = SongSearchParams(tag_ids={52, 481}, max_results=1)
    result = params.to_url_params()
    assert "tagId[]" in result
    assert isinstance(result["tagId[]"], list)
    assert set(result["tagId[]"]) == {"52", "481"}


def test_to_url_params_datetime_fields() -> None:
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    params = SongSearchParams(
        published_after_date=dt,
        max_results=1,
    )
    result = params.to_url_params()
    assert "afterDate" in result
    assert "2025-01-15" in str(result["afterDate"])


def test_to_url_params_does_not_mutate_original() -> None:
    params = SongSearchParams(query="test", max_results=10)
    params.to_url_params()
    assert params.max_results == 10
    assert params.query == "test"
