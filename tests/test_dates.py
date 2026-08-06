from reunion_companion.dates import decode_packed_date


def test_decode_year_only() -> None:
    date = decode_packed_date(bytes.fromhex("00 E0 9B 16"))
    assert date.day is None
    assert date.month is None
    assert date.year == 1976
    assert date.display == "1976"


def test_decode_month_year() -> None:
    date = decode_packed_date(bytes.fromhex("40 E1 9B 16"))
    assert date.day is None
    assert date.month == 5
    assert date.year == 1976
    assert date.display == "May 1976"


def test_decode_full_date() -> None:
    date = decode_packed_date(bytes.fromhex("44 E1 9B 16"))
    assert date.day == 4
    assert date.month == 5
    assert date.year == 1976
    assert date.display == "4 May 1976"


def test_decode_about_date() -> None:
    date = decode_packed_date(bytes.fromhex("40 E1 9B 16"), qualifier=0xA0)
    assert date.qualifier_name == "about"
    assert date.display == "abt May 1976"


def test_decode_older_year_with_high_flags() -> None:
    date = decode_packed_date(bytes.fromhex("42 14 9B 0C"))
    assert date.year == 1925
    assert date.month == 1
    assert date.day == 2
