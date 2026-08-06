from reunion_companion.dates import decode_packed_date


def test_decode_year_only() -> None:
    date = decode_packed_date(bytes.fromhex("00 E0 9B 16"))
    assert date.day is None
    assert date.month is None


def test_decode_month_year() -> None:
    date = decode_packed_date(bytes.fromhex("40 E1 9B 16"))
    assert date.day is None
    assert date.month == 5


def test_decode_full_date() -> None:
    date = decode_packed_date(bytes.fromhex("44 E1 9B 16"))
    assert date.day == 4
    assert date.month == 5
