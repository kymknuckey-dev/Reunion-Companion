from reunion_companion.companion.ryerson_surname_bootstrap import _result_surname,_rows_correspond_to_surname

def row(name):
    return {"source_record_name":name}

def test_result_surname_handles_real_knuckey_shapes():
    assert _result_surname("(Mrs H J) KNUCKEY")=="knuckey"
    assert _result_surname("A M (Bill) KNUCKEY")=="knuckey"
    assert _result_surname("[Alice] KNUCKEY")=="knuckey"

def test_requested_surname_rows_are_accepted():
    rows=[row("Annette SCHAPEL"),row("Brian Lawrence (Stumpy) SCHAPEL"),row("Bill SCHAPEL")]
    assert _rows_correspond_to_surname(rows,"Schapel")

def test_stale_previous_surname_page_is_rejected():
    rows=[row("Ada KNUCKEY"),row("Barbara KNUCKEY"),row("Bill KNUCKEY")]
    assert not _rows_correspond_to_surname(rows,"Mitchell")

def test_mixed_page_requires_ninety_percent_requested_surname():
    good=[row(f"Person {i} MITCHELL") for i in range(9)]
    bad=[row("One KNUCKEY")]
    assert _rows_correspond_to_surname(good+bad,"Mitchell")
    assert not _rows_correspond_to_surname(good[:8]+bad+bad,"Mitchell")

def test_empty_result_set_is_not_verified_as_transition():
    assert not _rows_correspond_to_surname([],"Mitchell")
