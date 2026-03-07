# ruff: noqa: S101


from vdbpy.utils.date import parse_date


def test_parse_date_iso_with_ms() -> None:
    assert (
        str(parse_date("2025-09-29T04:32:04.89"))
        == "2025-09-29 04:32:04.890000+00:00"
    )


def test_parse_date_iso_z() -> None:
    assert str(parse_date("2025-09-29T00:00:00Z")) == "2025-09-29 00:00:00+00:00"


def test_parse_date_no_z_suffix() -> None:
    assert str(parse_date("2025-09-28T12:47:09")) == "2025-09-28 12:47:09+00:00"


def test_parse_date_with_ms_and_z() -> None:
    assert (
        str(parse_date("2025-09-29T23:19:37.25Z"))
        == "2025-09-29 23:19:37.250000+00:00"
    )


def test_parse_date_three_digit_ms() -> None:
    assert (
        str(parse_date("2025-09-28T12:46:59.327"))
        == "2025-09-28 12:46:59.327000+00:00"
    )


def test_parse_date_with_positive_offset() -> None:
    assert (
        str(parse_date("2025-07-21T02:00:00+02:00"))
        == "2025-07-21 00:00:00+00:00"
    )


def test_parse_date_short_format() -> None:
    assert str(parse_date("2025-07-21")) == "2025-07-21 00:00:00+00:00"


def test_parse_date_formatted_am_pm() -> None:
    assert str(parse_date("01/25/2024 03:45 PM")) == "2024-01-25 15:45:00+00:00"


def test_parse_date_formatted_midnight() -> None:
    assert str(parse_date("06/01/2023 12:00 AM")) == "2023-06-01 00:00:00+00:00"
