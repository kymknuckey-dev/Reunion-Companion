from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.field_archaeology import (
    analyse_observations,
    rank_constant_bytes,
    rank_variable_bytes,
)


def _obs(person_id: int, context_hex: str) -> EventObservation:
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=0,
        record_length=100,
        marker_offset=24,
        raw_date_offset=31,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        signature="",
        context_hex=context_hex,
    )


def test_field_archaeology_finds_constant_and_variable_bytes() -> None:
    # 24 pre-marker bytes + 24 post-marker bytes.
    first = bytes([0] * 23 + [1] + [10] * 24)
    second = bytes([0] * 23 + [2] + [10] * 24)

    report = analyse_observations(
        [_obs(1, first.hex(" ")), _obs(2, second.hex(" "))],
        pre_bytes=24,
        post_bytes=24,
    )

    variable = report.byte_at(-1)
    constant = report.byte_at(0)

    assert variable is not None
    assert variable.distinct_values == 2
    assert constant is not None
    assert constant.is_constant is True
    assert constant.most_common_value == 10


def test_field_archaeology_ranking() -> None:
    first = bytes([0] * 23 + [1] + [10] * 24)
    second = bytes([0] * 23 + [2] + [10] * 24)
    report = analyse_observations(
        [_obs(1, first.hex(" ")), _obs(2, second.hex(" "))],
        pre_bytes=24,
        post_bytes=24,
    )

    variables = rank_variable_bytes(report, minimum_samples=1)
    constants = rank_constant_bytes(report, minimum_samples=1)

    assert any(item.relative_offset == -1 for item in variables)
    assert any(item.relative_offset == 0 for item in constants)
