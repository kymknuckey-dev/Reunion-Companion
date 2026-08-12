from __future__ import annotations

"""FFD 1.7 Build 2.2 — evidence-aware narrative synthesis.

The conversation layer is allowed to retell Reunion-authored information in new
wording, but it must remain faithful to the imported facts.  Reunion object
identity and note type are treated as provenance, not inferred from keywords.
"""

import re
from typing import Any
from .person_knowledge import assemble_person_knowledge


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _sentences(text: str) -> list[str]:
    text = _clean(text)
    if not text:
        return []
    # Sentence extraction is intentionally lossless with respect to the source
    # text.  Answer length is controlled by sentence selection, not by cutting
    # evidence at an arbitrary character boundary.
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


def _event_kind(e):
    return _clean(e.get("event_type") or e.get("type") or e.get("gedcom_tag")).casefold()


def _event_text(e):
    label = _clean(e.get("event_type") or e.get("type") or e.get("gedcom_tag") or "Event")
    date = _clean(e.get("date_text") or e.get("date") or e.get("date_display"))
    place = _clean(e.get("place_text") or e.get("place") or e.get("place_name"))
    value = _clean(e.get("value_text") or e.get("value") or e.get("description"))
    bits = [x for x in (date, place, value) if x]
    return f"{label}: " + (" — ".join(bits) if bits else "recorded")


def _relationship_map(k):
    out = {}
    for r in k.get("relationships", []):
        rel = _clean(r.get("relationship")); name = _clean(r.get("display_name"))
        if rel and name:
            out.setdefault(rel, []).append(name)
    return out


def _dedupe(items):
    out = []; seen = set()
    for x in items:
        text = _clean(x)
        key = text.casefold()
        if key and key not in seen:
            seen.add(key); out.append(text)
    return out


def _note_provenance(note) -> str:
    """Return Reunion's own note/object label wherever one exists."""
    raw = _clean(note.get("note_type") or note.get("title") or note.get("gedcom_tag") or "Note")
    low = raw.casefold()
    if low in ("note", "misc note", "misc notes", "_note"):
        return "Misc Notes" if "misc" in low else "general life notes"
    if low == "research":
        return "research notes"
    return raw


def _note_label_for_topic(label: str) -> str:
    low = label.casefold()
    if any(x in low for x in ("military", "army", "navy", "service")):
        return "military"
    if any(x in low for x in ("medical", "health")):
        return "medical"
    if any(x in low for x in ("occupation", "employment", "career", "work")):
        return "work"
    if any(x in low for x in ("migration", "immigration", "emigration", "residence")):
        return "migration"
    if "research" in low:
        return "research"
    return "general"


_TOPIC_TERMS = {
    "work": ("occupation", "work", "worked", "working", "career", "job", "trade", "profession", "employ", "retired", "retirement", "clerk", "apprent", "public servant"),
    "marriage": ("marriage", "married", "wedding", "wife", "husband", "spouse"),
    "military": ("military", "army", "navy", "air force", "war", "service", "enlist", "battalion", "regiment", "aif", "raaf", "ran"),
    "medical": ("medical", "health", "hospital", "illness", "disease", "cardiac", "heart", "surgery", "admitted"),
    "migration": ("migration", "immigration", "emigration", "arrival", "arrived", "moved", "residence", "settled"),
}


def _sentence_matches_topic(sentence: str, topic: str) -> bool:
    low = sentence.casefold()
    return any(term in low for term in _TOPIC_TERMS.get(topic, (topic,)))


def _select_note_sentences(note, topic: str | None = None, budget: int = 7) -> list[str]:
    """Select complete source sentences without character truncation.

    A note explicitly typed by Reunion for the requested topic is primary
    evidence and is read independently of keyword matches.  Other note types
    can contribute corroborating sentences when those sentences are relevant.
    """
    sentences = _sentences(note.get("text"))
    if not sentences:
        return []
    label = _note_provenance(note)
    typed_topic = _note_label_for_topic(label)

    if topic and typed_topic == topic:
        # Reunion has already told us what kind of object this is.  Keep enough
        # complete sentences to form a useful account; do not reclassify it.
        return _dedupe(sentences[:budget])

    if topic:
        matches = [s for s in sentences if _sentence_matches_topic(s, topic)]
        return _dedupe(matches[:budget])

    # General notes overview: give each authored object a compact but useful
    # account.  Preserve opening context, information-rich middle statements,
    # and an ending statement rather than cutting at a character count.
    if len(sentences) <= budget:
        return _dedupe(sentences)
    chosen = sentences[:2]
    informative = []
    for s in sentences[2:-1]:
        low = s.casefold()
        if (re.search(r"\b(?:18|19|20)\d{2}\b", s)
                or any(term in low for terms in _TOPIC_TERMS.values() for term in terms)):
            informative.append(s)
    chosen.extend(informative[:max(0, budget - 3)])
    chosen.append(sentences[-1])
    return _dedupe(chosen[:budget])


def _note_evidence(k, topic: str | None = None, budget_per_note: int = 7):
    out = []
    for n in k.get("notes", []):
        selected = _select_note_sentences(n, topic=topic, budget=budget_per_note)
        if selected:
            out.append({
                "label": _note_provenance(n),
                "typed_topic": _note_label_for_topic(_note_provenance(n)),
                "sentences": selected,
                "note_id": n.get("id"),
            })
    # For topic answers, evidence explicitly typed for the topic comes first.
    if topic:
        out.sort(key=lambda x: (0 if x["typed_topic"] == topic else 1, str(x["label"]).casefold(), x.get("note_id") or 0))
    return out


def _provenance_line(labels) -> str:
    labels = _dedupe(labels)
    return "Based on: " + " · ".join(labels) if labels else ""


def _natural_join(items: list[str]) -> str:
    items = [x for x in _dedupe(items) if x]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + " and " + items[1]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _life_overview(k):
    name = _clean(k["person"].get("display_name")) or "This person"
    events = k.get("events", []); rel = _relationship_map(k)
    parts = []
    provenance = []

    birth = next((e for e in events if "birth" in _event_kind(e)), None)
    death = next((e for e in events if "death" in _event_kind(e)), None)
    opening = f"Reunion records {name}."
    life = []
    if birth:
        life.append(_event_text(birth)); provenance.append("Birth")
    if death:
        life.append(_event_text(death)); provenance.append("Death")
    if life:
        opening += " " + "; ".join(life) + "."
    parts.append(opening)

    family = []
    if rel.get("Spouse"):
        family.append("spouse " + ", ".join(rel["Spouse"])); provenance.append("Family relationships")
    children = rel.get("Son", []) + rel.get("Daughter", []) + rel.get("Child", [])
    if children:
        family.append(f"{len(children)} recorded child" + ("ren" if len(children) != 1 else "")); provenance.append("Family relationships")
    parents = rel.get("Father", []) + rel.get("Mother", []) + rel.get("Parent", [])
    if parents:
        family.append("parents " + " and ".join(parents)); provenance.append("Family relationships")
    if family:
        parts.append("Family information identifies " + "; ".join(family) + ".")

    notable = []
    for e in events:
        if any(x in _event_kind(e) for x in ("birth", "death", "burial")):
            continue
        notable.append(_event_text(e))
    if notable:
        parts.append("Other structured facts include " + "; ".join(_dedupe(notable)[:6]) + ".")
        provenance.extend([_clean(e.get("event_type") or e.get("gedcom_tag") or "Event") for e in events if not any(x in _event_kind(e) for x in ("birth", "death", "burial"))])

    notes = _note_evidence(k, budget_per_note=3)
    if notes:
        note_bits = []
        for item in notes[:4]:
            note_bits.append(f"{item['label']}: " + " ".join(item["sentences"]))
            provenance.append(item["label"])
        parts.append("The authored notes add further context. " + " ".join(note_bits))

    p = _provenance_line(provenance)
    if p:
        parts.append(p)
    return "\n\n".join(parts)


def _notes_answer(k):
    name = _clean(k["person"].get("display_name")); notes = k.get("notes", [])
    if not notes:
        return f"No authored notes are currently linked to {name} in the Companion database."
    evidence = _note_evidence(k, budget_per_note=7)
    if not evidence:
        return f"Notes are linked to {name}, but they contain no readable text in the current import."

    # Compatibility with earlier Build 2.1 wording while changing the actual
    # behaviour from theme guessing to object-aware evidence synthesis.
    categories = _dedupe([item["label"] if item["label"] != "general life notes" else "general life notes" for item in evidence])
    intro = (f"Reunion has {len(notes)} authored note{'s' if len(notes) != 1 else ''} for {name}. "
             f"Rather than repeating them verbatim, the answer below keeps Reunion's own note types separate and summarises the facts they contain.")
    if categories:
        intro += " The note areas are: " + ", ".join(categories) + "."

    body = []
    for item in evidence:
        body.append(f"{item['label']}: " + " ".join(item["sentences"]))
    body.append(_provenance_line([x["label"] for x in evidence]))
    return intro + "\n\n" + "\n\n".join(x for x in body if x)


def _marriage_family_details(k):
    rel = _relationship_map(k); spouses = rel.get("Spouse", [])
    bits = []
    if spouses:
        bits.append("Recorded spouse" + ("s" if len(spouses) > 1 else "") + ": " + ", ".join(spouses))
    fams = [f for f in k.get("families", []) if any(r in (f.get("person_roles") or []) for r in ("husband", "wife", "spouse"))]
    for f in fams:
        d = _clean(f.get("marriage_date")); p = _clean(f.get("marriage_place"))
        if d and p:
            bits.append(f"Marriage recorded on {d} at {p}")
        elif d:
            bits.append(f"Marriage recorded on {d}")
        elif p:
            bits.append(f"Marriage place recorded as {p}")
    return _dedupe(bits)


def _topic_answer(k, topic):
    name = _clean(k["person"].get("display_name")); topic = topic.casefold(); events = k.get("events", [])
    terms = {
        "work": ("occupation", "work", "career", "trade", "profession"),
        "marriage": ("marriage", "married", "wedding"),
        "military": ("military", "service", "army", "navy", "war", "enlist"),
        "medical": ("medical", "health", "hospital", "illness"),
        "migration": ("immigration", "emigration", "migration", "arrival", "arrived", "moved"),
    }.get(topic, (topic,))

    event_hits = []
    event_labels = []
    for e in events:
        blob = " ".join(_clean(e.get(x)) for x in ("event_type", "value_text", "note_text", "place_text")).casefold()
        if any(t in blob for t in terms):
            event_hits.append(_event_text(e)); event_labels.append(_clean(e.get("event_type") or e.get("gedcom_tag") or "Event"))
    if topic == "marriage":
        family_bits = _marriage_family_details(k)
        event_hits = family_bits + event_hits
        if family_bits:
            event_labels.append("Family marriage record")

    note_evidence = _note_evidence(k, topic=topic, budget_per_note=9)
    if not event_hits and not note_evidence:
        return f"I could not find Reunion information about {name}’s {topic} in the currently assembled knowledge."

    label = {"work": "working life", "marriage": "marriage", "military": "military service", "medical": "medical history", "migration": "migration"}.get(topic, topic)
    out = [f"Reunion records the following about {name}’s {label}."]

    if event_hits:
        # Keep the exact structured fact representation so precise Reunion facts
        # remain visible inside the more natural narrative answer.
        out.append(" ".join(_dedupe(event_hits)) + ".")

    if note_evidence:
        paragraphs = []
        for item in note_evidence:
            paragraphs.append(f"{item['label']}: " + " ".join(item["sentences"]))
        out.extend(paragraphs)

    provenance = event_labels + [x["label"] for x in note_evidence]
    p = _provenance_line(provenance)
    if p:
        out.append(p)
    return "\n\n".join(out)


def interpret_knowledge_question(question):
    low = " ".join(_clean(question).casefold().replace("’", "'").split())
    if not low:
        return None
    if low in ("tell me more about that", "tell me more", "more about that", "what else do we know about that"):
        return "followup"
    if "what do the notes say" in low or "what do notes say" in low or "show me the notes" in low or "tell me the notes" in low:
        return "notes"
    if any(p in low for p in ("tell me about", "what do you know about", "what do we know about", "life story", "biography")):
        if any(x in low for x in ("working life", "work", "career", "occupation", "job", "trade")):
            return "topic:work"
        if any(x in low for x in ("marriage", "wedding", "married")):
            return "topic:marriage"
        if any(x in low for x in ("military", "army", "navy", "war service", "service life")):
            return "topic:military"
        if any(x in low for x in ("medical", "health", "hospital", "illness")):
            return "topic:medical"
        if any(x in low for x in ("migration", "immigration", "emigration", "arrival", "moved")):
            return "topic:migration"
        return "overview"
    return None


def answer_knowledge_question(db, person_id, question, prior_intent=None):
    intent = interpret_knowledge_question(question)
    if not intent:
        return None
    if intent == "followup":
        if not prior_intent:
            return {"status": "unsupported", "kind": "knowledge", "answer": "Tell me which part you would like to explore further."}
        intent = prior_intent
    k = assemble_person_knowledge(db, person_id)
    if not k:
        return {"status": "not-found", "kind": "knowledge", "answer": "I could not assemble Reunion knowledge for that person."}
    if intent == "notes":
        answer = _notes_answer(k)
    elif intent.startswith("topic:"):
        answer = _topic_answer(k, intent.split(":", 1)[1])
    else:
        answer = _life_overview(k)
    return {
        "status": "ok",
        "kind": "knowledge",
        "knowledge_intent": intent,
        "answer": answer,
        "knowledge_counts": k.get("counts", {}),
        "grounding": "Reunion Person Knowledge",
        "narrative_generated": True,
        "synthesis_mode": "evidence-aware",
    }
