from __future__ import annotations

from .models import ReunionDate

_QUALIFIERS = {
    0x00: None,
    0xA0: "about",
}

_MONTHS = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def format_reunion_date(
    year: int,
    month: int | None,
    day: int | None,
    qualifier_name: str | None = None,
) -> str:
    parts: list[str] = []
    if qualifier_name:
        parts.append("abt" if qualifier_name == "about" else qualifier_name)

    if day is not None and month is not None:
        parts.extend([str(day), _MONTHS[month], str(year)])
    elif month is not None:
        parts.extend([_MONTHS[month], str(year)])
    else:
        parts.append(str(year))
    return " ".join(parts)


def decode_packed_date(raw: bytes, qualifier: int | None = None) -> ReunionDate:
    """Decode the packed Reunion date observed in the controlled Reunion 14 probes.

    Proven lower-bit layout:
      bits 0-5: day, zero when absent
      bits 6-9: month, zero when absent
      bits 10-20: year minus 192
      bits 21+: flags not yet decoded

    Qualifier byte 0xA0 has been observed for ``abt``. Exact dates use 0x00.
    """
    if len(raw) != 4:
        raise ValueError(f"Packed date must be exactly 4 bytes, received {len(raw)}")

    value = int.from_bytes(raw, byteorder="little", signed=False)
    day_value = value & 0x3F
    month_value = (value >> 6) & 0x0F
    year_code = (value >> 10) & 0x07FF
    high_flags = value >> 21
    year = year_code + 192

    day = day_value or None
    month = month_value or None

    if day is not None and not 1 <= day <= 31:
        raise ValueError(f"Invalid packed day value: {day}")
    if month is not None and not 1 <= month <= 12:
        raise ValueError(f"Invalid packed month value: {month}")
    if not 1 <= year <= 4095:
        raise ValueError(f"Implausible packed year value: {year}")

    qualifier_name = _QUALIFIERS.get(qualifier)
    display = format_reunion_date(year, month, day, qualifier_name)

    return ReunionDate(
        raw_value=value,
        day=day,
        month=month,
        year=year,
        year_code=year_code,
        high_flags=high_flags,
        qualifier=qualifier,
        qualifier_name=qualifier_name,
        display=display,
    )
