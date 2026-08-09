from reunion_companion.discovery.differential_verification import ByteSpanDelta, DecodedEventDelta, DifferentialResult
from reunion_companion.discovery.noise_suppression import suppress_noise

def span(b, a, start=100, n=20):
    return ByteSpanDelta("replace", start, start+n, start, start+n, "00", "01", b, a)

def result(spans, decoded=()):
    return DifferentialResult("Birth Date","before","after","b","a",1000,1000,tuple(spans),
                              sum(x.before_length for x in spans),
                              sum(x.after_length for x in spans),
                              tuple(decoded),(),())

def test_path_and_ui_suppressed():
    x = suppress_noise(result([
        span("/Users/kym/A.familyfile14", "/Users/kym/B.familyfile14"),
        span("NSMutableDictionary LucidaGrande", "NSDictionary LucidaGrande", 300),
    ]))
    assert len(x.noise_spans) == 2

def test_place_token_semantic():
    x = suppress_noise(result([span("[[pt:1]] Probe reference", "[[pt:2]] Probe reference")]))
    assert x.semantic_spans
    assert x.semantic_spans[0].category == "TEXT_SEMANTIC_CANDIDATE"

def test_decoded_event_nearby_semantic():
    e = DecodedEventDelta(1,"Test Probe","2 Jan 1925","2 Jan 1926","[[pt:1]]","[[pt:1]]",
                          0,0,500,500,"date value changed")
    x = suppress_noise(result([span("....","....",520)], [e]))
    assert x.semantic_spans[0].category == "DECODED_EVENT"
