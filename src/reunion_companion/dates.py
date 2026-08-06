from __future__ import annotations

from .models import ReunionDate


def decode_packed_date(raw: bytes, qualifier: int | None = None) -> ReunionDate:
    """Decode the currently understood portion of a Reunion packed date.

    This function intentionally exposes `year_code` rather than claiming a
    calendar year until the fixed offset and high-bit semantics are proven.
    """
    if len(raw) != 4:
        raise ValueError(f"Packed date must be exactly 4 bytes, received {len(raw)}")

    value = int.from_bytes(raw, byteorder="little", signed=False)
    day_value = value & 0x3F
    month_value = (value >> 6) & 0x0F
    year_code = value >> 10

    day = day_value or None
    month = month_value or None

    if day is not None and not 1 <= day <= 31:
        raise ValueError(f"Invalid packed day value: {day}")
    if month is not None and not 1 <= month <= 12:
        raise ValueError(f"Invalid packed month value: {month}")

    return ReunionDate(
        raw_value=value,
        day=day,
        month=month,
        year_code=year_code,
        qualifier=qualifier,
    )
