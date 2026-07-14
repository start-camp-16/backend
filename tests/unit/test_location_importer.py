import pytest

from app.locations.importer import extract_district, parse_float


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("서울특별시 강남구 테헤란로", "강남구"),
        ("서울 마포구 월드컵로", "마포구"),
        ("부산광역시 해운대구", "기타"),
        ("", "기타"),
        (None, "기타"),
    ],
)
def test_extract_district(address, expected):
    assert extract_district(address) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("127.01", 127.01), (0, 0.0), ("", None), (None, None), ("invalid", None)],
)
def test_parse_float(value, expected):
    assert parse_float(value) == expected
