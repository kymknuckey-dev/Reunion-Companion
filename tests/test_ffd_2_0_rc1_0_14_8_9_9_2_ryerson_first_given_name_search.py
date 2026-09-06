from reunion_companion.companion.ryerson_adapter import (
    RyersonQuery,
    build_ryerson_queries,
    search_ryerson,
)


def test_multiple_given_names_produce_one_first_name_query():
    assert build_ryerson_queries({"surname": "Beckmann", "given_names": "Charles Otto"}) == [
        RyersonQuery("Beckmann", "Charles", "")
    ]


def test_three_given_names_still_produce_one_first_name_query():
    assert build_ryerson_queries({"surname": "Child", "given_names": "Victoria Mary Sophia"}) == [
        RyersonQuery("Child", "Victoria", "")
    ]


def test_blank_given_name_preserves_surname_only_query():
    assert build_ryerson_queries({"surname": "Knuckey", "given_names": ""}) == [
        RyersonQuery("Knuckey", "", "")
    ]


def test_search_transport_is_called_once_for_multiple_given_names():
    calls=[]

    def fetch(query):
        calls.append(query)
        return 200, "<table></table>"

    assert search_ryerson({"surname": "Rigg", "given_names": "Peter Stanley"}, fetch) == []
    assert calls == [RyersonQuery("Rigg", "Peter", "")]
