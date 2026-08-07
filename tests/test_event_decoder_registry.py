from reunion_companion.records import PERSON_EVENT_DECODERS


def test_person_event_decoder_registry_starts_with_birth() -> None:
    assert len(PERSON_EVENT_DECODERS) >= 1
    assert PERSON_EVENT_DECODERS[0].__name__ == "_decode_birth_event"
