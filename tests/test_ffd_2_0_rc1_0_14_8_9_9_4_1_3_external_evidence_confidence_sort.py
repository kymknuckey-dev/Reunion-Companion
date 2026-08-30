from reunion_companion.companion.ryerson_discovery_ui import sort_grouped_people_recent


class Row(dict):
    pass


class DB:
    def execute(self, sql, args=()):
        class Result:
            def __init__(self, confidence): self.confidence=confidence
            def fetchone(self): return {"confidence": self.confidence}
        return Result({1:75,2:100,3:100}.get(int(args[0]),0))


def candidate(pid,name,date):
    return Row(person_id=pid,display_name=name,raw_name=name,proposed_fact_key=f"death:{date}",id=pid)


def test_recent_review_prioritises_confidence_then_date():
    grouped=[
        (1,[candidate(1,"Newest 75","2025-01-01")]),
        (2,[candidate(2,"Older 100","2020-01-01")]),
        (3,[candidate(3,"Newer 100","2024-01-01")]),
    ]
    ordered=sort_grouped_people_recent(grouped,DB())
    assert [p for p,_ in ordered]==[3,2,1]

def test_recent_review_copy_explains_confidence_priority():
    from pathlib import Path
    text=Path("src/reunion_companion/companion/ryerson_discovery_ui.py").read_text()
    assert "100% matches are shown before 75% matches" in text
