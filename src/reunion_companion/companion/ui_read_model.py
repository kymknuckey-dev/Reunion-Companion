from __future__ import annotations
from .family_publication_model import life_dates,person_events,person_notes,person_sources,person_media
from .research_intelligence import confidence_for_person

def person_workspace_model(db,pid):
    """Stable read model for the future Beta UI.

    It deliberately contains no write operations. Reunion remains authoritative.
    """
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    if not p:
        return None
    dates=life_dates(db,pid)
    events=[dict(x) for x in person_events(db,pid)]
    notes=[dict(x) for x in person_notes(db,pid)]
    sources=[dict(x) for x in person_sources(db,pid)]
    media=[dict(x) for x in person_media(db,pid)]
    try:
        confidence=confidence_for_person(db,pid)
    except Exception:
        confidence=None
    return {
        "person":{"id":p["id"],"name":p["display_name"],"sex":p["sex"]},
        "life":dates,
        "events":events,
        "notes":notes,
        "sources":sources,
        "media":media,
        "confidence":confidence,
    }
