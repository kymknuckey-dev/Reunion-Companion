from __future__ import annotations

"""FFD 1.7 Build 3 — local LLM-grounded genealogical conversation.

Reunion remains authoritative. Deterministic code resolves identity, facts,
relationships and evidence. A local Ollama model is used only to understand and
retell the selected Reunion evidence in natural prose.
"""

import re
from typing import Any

from .local_llm import LocalLLMError, OllamaClient
from .person_knowledge import assemble_person_knowledge


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


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
        text = _clean(x); key = text.casefold()
        if key and key not in seen:
            seen.add(key); out.append(text)
    return out


def _note_provenance(note) -> str:
    raw = _clean(note.get("note_type") or note.get("title") or note.get("gedcom_tag") or "Note")
    low = raw.casefold()
    if low in ("note", "misc note", "misc notes", "_note"):
        return "Misc Notes" if "misc" in low else "General Notes"
    if low == "research":
        return "Research Notes"
    return raw


def _note_topic(label: str) -> str:
    low = label.casefold()
    if any(x in low for x in ("military", "army", "navy", "war service")): return "military"
    if any(x in low for x in ("medical", "health")): return "medical"
    if any(x in low for x in ("occupation", "employment", "career", "work")): return "work"
    if any(x in low for x in ("migration", "immigration", "emigration", "residence")): return "migration"
    if any(x in low for x in ("marriage", "wedding")): return "marriage"
    if any(x in low for x in ("sport", "sporting", "athletic")): return "sport"
    return "general"


_TOPIC_TERMS = {
    "work": ("occupation", "worked", "working", "career", "job", "trade", "profession", "employ", "retired", "clerk", "apprentice", "public servant"),
    "marriage": ("marriage", "married", "wedding", "wife", "husband", "spouse"),
    "military": ("military", "army", "navy", "air force", "war", "enlist", "battalion", "regiment", "aif", "raaf", "ran", "discharge", "service number"),
    "medical": ("medical", "health", "hospital", "illness", "disease", "cardiac", "heart", "surgery", "admitted"),
    "migration": ("migration", "immigration", "emigration", "arrival", "arrived", "moved", "settled"),
    "residence": ("residence", "resident", "resided", "lived", "living", "address", "home", "house", "street", "road", "avenue", "court", "drive", "lane", "terrace", "built a home", "built new homes", "moved into", "moved to", "settled", "retirement village", "leased residence"),
    "golf": ("golf", "golfing", "golf club"),
    "netball": ("netball", "basketball", "women\'s basketball"),
}


def _sentences(text: str) -> list[str]:
    text = str(text or "").strip()
    if not text: return []
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


def _supporting_passages(text: str, topic: str) -> str:
    terms = _TOPIC_TERMS.get(topic, (topic,))
    hits = [s for s in _sentences(text) if any(term in s.casefold() for term in terms)]
    return " ".join(_dedupe(hits))


def _marriage_family_details(k):
    rel = _relationship_map(k); spouses = rel.get("Spouse", [])
    bits = []
    if spouses:
        bits.append("Recorded spouse" + ("s" if len(spouses) > 1 else "") + ": " + ", ".join(spouses))
    for f in k.get("families", []):
        if not any(r in (f.get("person_roles") or []) for r in ("husband", "wife", "spouse")):
            continue
        d = _clean(f.get("marriage_date")); p = _clean(f.get("marriage_place"))
        if d and p: bits.append(f"Marriage recorded on {d} at {p}")
        elif d: bits.append(f"Marriage recorded on {d}")
        elif p: bits.append(f"Marriage place recorded as {p}")
    return _dedupe(bits)


def _structured_evidence(k, topic: str | None) -> list[tuple[str, str]]:
    evidence: list[tuple[str, str]] = []
    events = k.get("events", [])
    if topic == "marriage":
        for line in _marriage_family_details(k): evidence.append(("Family marriage record", line))
    if topic == "research-gaps":
        for e in events:
            evidence.append((_clean(e.get("event_type") or e.get("gedcom_tag") or "Event"), _event_text(e)))
        # Research-gap analysis must know the recorded family context. Otherwise a
        # sparse event list can make the narrative model incorrectly claim that a
        # spouse, child or parent is missing even though Reunion records them.
        rel = _relationship_map(k)
        for label in ("Father", "Mother", "Spouse", "Son", "Daughter", "Child"):
            if rel.get(label):
                evidence.append(("Family relationships", f"{label}: {', '.join(rel[label])}"))
        for line in _marriage_family_details(k):
            evidence.append(("Family marriage record", line))
        for c in k.get("citations", []):
            label=_clean(c.get("source_display_text") or c.get("source_title") or c.get("source_xref") or "Citation")
            if label: evidence.append(("Evidence", label))
        return evidence
    for e in events:
        kind = _event_kind(e)
        blob = " ".join(_clean(e.get(x)) for x in ("event_type", "value_text", "note_text", "place_text")).casefold()
        if topic is None:
            if any(x in kind for x in ("birth", "death", "occupation", "residence", "marriage", "military")):
                evidence.append((_clean(e.get("event_type") or e.get("gedcom_tag") or "Event"), _event_text(e)))
        elif any(term in blob for term in _TOPIC_TERMS.get(topic, (topic,))):
            # Domain words can appear incidentally in unrelated values (for example
            # "S.A. Health Commission" is an occupation, not medical evidence).
            if topic == "medical" and any(x in kind for x in ("occupation", "occup")):
                continue
            evidence.append((_clean(e.get("event_type") or e.get("gedcom_tag") or "Event"), _event_text(e)))
    if topic is None:
        rel = _relationship_map(k)
        for label in ("Father", "Mother", "Spouse", "Son", "Daughter", "Child"):
            if rel.get(label): evidence.append(("Family relationships", f"{label}: {', '.join(rel[label])}"))
    return evidence


def _note_documents(k, topic: str | None, notes_overview: bool = False) -> list[dict[str, str]]:
    docs = []
    for n in k.get("notes", []):
        label = _note_provenance(n)
        text = str(n.get("text") or "").strip()
        if not text: continue
        typed = _note_topic(label)
        if notes_overview or topic is None:
            selected = text
        elif typed == topic:
            selected = text
        elif typed == "sport" and topic in ("golf", "netball", "sport"):
            selected = _supporting_passages(text, topic) or text
        elif typed == "general":
            selected = _supporting_passages(text, topic)
        else:
            # A Medical note, for example, must not leak into a military answer
            # merely because it contains a generic word such as "service".
            selected = ""
        if selected:
            docs.append({"label": label, "text": selected, "typed_topic": typed})
    if topic:
        docs.sort(key=lambda d: (0 if d["typed_topic"] == topic else 1, d["label"].casefold()))
    return docs


def _chunk_text(text: str, limit: int = 8000) -> list[str]:
    text = str(text or "").strip()
    if len(text) <= limit: return [text] if text else []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) <= 1: paragraphs = _sentences(text)
    chunks=[]; current=[]; size=0
    for p in paragraphs:
        if current and size + len(p) + 2 > limit:
            chunks.append("\n\n".join(current)); current=[]; size=0
        if len(p) > limit:
            if current: chunks.append("\n\n".join(current)); current=[]; size=0
            for i in range(0, len(p), limit): chunks.append(p[i:i+limit])
            continue
        current.append(p); size += len(p) + 2
    if current: chunks.append("\n\n".join(current))
    return chunks


_GROUNDING_RULES = """You are the narrative layer for Reunion Companion, a genealogy application.
Use ONLY the supplied Reunion evidence. Do not add facts from general knowledge and do not guess missing details.
You may freely rewrite, reorganise and combine the evidence. Preserve uncertainty and differing recollections where they exist.
Do not reproduce long passages verbatim. Write natural, readable prose that answers the user's question directly.
Do not mention evidence that is irrelevant to the question. A source labelled Medical Notes is not military evidence; a source labelled Military Notes is primary military evidence.
Do not say that you searched the internet. The evidence came only from the user's local Reunion database.
If the evidence is insufficient, say so plainly.
"""


def _condense_long_document(client: OllamaClient, label: str, text: str, question: str) -> str:
    chunks = _chunk_text(text)
    if len(chunks) <= 1: return text
    summaries=[]
    for idx, chunk in enumerate(chunks, 1):
        prompt = f"""{_GROUNDING_RULES}
The following is chunk {idx} of {len(chunks)} from Reunion source [{label}].
Extract the factual information from this chunk that is relevant to the question. Use concise new wording. Do not omit dates, places, names, jobs, units or other concrete facts that matter.

Question: {question}

[{label} — chunk {idx}]
{chunk}

Relevant factual digest:"""
        summaries.append(client.generate(prompt))
    return "\n".join(summaries)


def _synthesis_prompt(name: str, question: str, structured, notes, intent: str) -> str:
    parts = [_GROUNDING_RULES]
    if intent == "notes":
        parts.append("The user asked what the notes say. Give a useful overview of the main subjects in the notes, then briefly summarise each important area. Do not dump each note in sequence.")
    elif intent == "research:gaps":
        parts.append("Assess the recorded life timeline as a research aid. Identify notable periods with sparse or missing recorded events, facts lacking obvious supporting evidence, and areas that may merit further research. Do not claim that an event did not happen merely because it is absent from Reunion. Distinguish a gap in the record from a fact about the person. Treat the supplied family relationships as known recorded facts: never report a spouse, child or parent as missing when that relationship appears in the evidence.")
    elif intent.startswith("topic:"):
        parts.append("Focus tightly on the requested topic. Prefer explicitly typed Reunion notes for that topic, and use general notes only as supporting evidence when relevant.")
    else:
        parts.append("Give a concise life overview, organised into natural themes rather than a database-field list.")
    parts.append(f"Person: {name}\nQuestion: {question}")
    if structured:
        parts.append("STRUCTURED REUNION EVIDENCE:\n" + "\n".join(f"[{label}] {text}" for label, text in structured))
    if notes:
        parts.append("AUTHORED REUNION NOTES:\n" + "\n\n".join(f"[{d['label']}]\n{d['text']}" for d in notes))
    parts.append("Write the answer now. Do not include a 'Based on' line; Reunion Companion adds provenance separately.")
    return "\n\n".join(parts)


def _provenance(structured, notes) -> list[str]:
    return _dedupe([label for label, _ in structured] + [d["label"] for d in notes])


def interpret_knowledge_question(question):
    low = " ".join(_clean(question).casefold().replace("’", "'").split())
    if not low: return None
    if low in ("tell me more about that", "tell me more", "more about that", "what else do we know about that"):
        return "followup"
    if "what do the notes say" in low or "what do notes say" in low or "show me the notes" in low or "tell me the notes" in low:
        return "notes"

    # FFD 1.8 Build 1.1: route by the question's evidence domain before
    # a generic structured-field matcher can return an unrelated fact.
    if any(x in low for x in ("health issue", "health issues", "illness", "illnesses", "medical", "heart attack", "hospital", "disease", "health problems")):
        return "topic:medical"
    if any(x in low for x in ("military", "army", "navy", "air force", "war", "wars", "conflict", "conflicts", "national service", "enlisted", "service life")):
        return "topic:military"
    if any(x in low for x in ("where did he live", "where did she live", "where did they live", "where lived", "residence", "residences", "addresses", "address", "homes during", "lived during")):
        return "topic:residence"
    if any(x in low for x in ("golf", "golfing")):
        return "topic:golf"
    if any(x in low for x in ("netball", "women's basketball")):
        return "topic:netball"
    if any(x in low for x in ("gaps in the timeline", "gaps in timeline", "need more search work", "need more research", "research gaps", "timeline gaps")):
        return "research:gaps"

    if any(p in low for p in ("tell me about", "what do you know about", "what do we know about", "life story", "biography")):
        if any(x in low for x in ("working life", "work", "career", "occupation", "job", "trade")): return "topic:work"
        if any(x in low for x in ("marriage", "wedding", "married")): return "topic:marriage"
        if any(x in low for x in ("migration", "immigration", "emigration", "arrival", "moved")): return "topic:migration"
        return "overview"
    return None


def _inherit_prior_topic(question: str, prior_intent: str | None) -> str | None:
    """Conservatively inherit an established story topic for short follow-ups.

    This is intentionally narrower than treating every pronoun question as a
    follow-up. Explicit domains (birth, death, health, residence, etc.) still win
    through interpret_knowledge_question(), while forms such as "Did she play for
    Australia?", "When did she start?" and "How long did she play?" can
    continue the prior netball/golf topic instead of falling into a random
    structured-fact route.
    """
    if not prior_intent or not str(prior_intent).startswith("topic:"):
        return None
    low = " ".join(_clean(question).casefold().replace("’", "'").split())
    if not low or len(low.split()) > 10:
        return None
    patterns = (
        r"^(did|does|was|were)\s+(he|she|they)\b",
        r"^(when|where|who)\s+did\s+(he|she|they)\b",
        r"^how\s+(long|often|well)\s+did\s+(he|she|they)\b",
        r"^(when|where|who|how)\s+(was|were)\s+(he|she|they)\b",
    )
    if any(re.search(p, low) for p in patterns):
        return prior_intent
    return None


def answer_knowledge_question(db, person_id, question, prior_intent=None, client: OllamaClient | None = None):
    intent = interpret_knowledge_question(question)
    if not intent:
        intent = _inherit_prior_topic(question, prior_intent)
    if not intent: return None
    if intent == "followup":
        if not prior_intent:
            return {"status": "unsupported", "kind": "knowledge", "answer": "Tell me which part you would like to explore further."}
        intent = prior_intent

    k = assemble_person_knowledge(db, person_id)
    if not k:
        return {"status": "not-found", "kind": "knowledge", "answer": "I could not assemble Reunion knowledge for that person."}

    topic = intent.split(":", 1)[1] if intent.startswith("topic:") else ("research-gaps" if intent == "research:gaps" else None)
    notes_overview = intent == "notes"
    structured = _structured_evidence(k, topic)
    notes = _note_documents(k, topic, notes_overview=notes_overview)
    if not structured and not notes:
        name = _clean(k.get("person", {}).get("display_name")) or "that person"
        return {"status": "not-found", "kind": "knowledge", "knowledge_intent": intent,
                "answer": f"I could not find Reunion evidence that answers that question about {name}."}

    local = client or OllamaClient()
    try:
        prepared=[]
        for d in notes:
            prepared.append({**d, "text": _condense_long_document(local, d["label"], d["text"], question)})
        name = _clean(k["person"].get("display_name")) or "This person"
        answer = local.generate(_synthesis_prompt(name, question, structured, prepared, intent)).strip()
        labels = _provenance(structured, notes)
        if labels:
            answer += "\n\nBased on: " + " · ".join(labels)
        model = local.resolve_model()
    except LocalLLMError as exc:
        # Keep the previous deterministic renderer as an explicit degraded mode.
        # This preserves older installations/tests and still gives the user access
        # to Reunion evidence if Ollama is stopped, while making clear that true
        # narrative synthesis is unavailable.
        from .knowledge_conversation_legacy import answer_knowledge_question as legacy_answer
        fallback = legacy_answer(db, person_id, question, prior_intent=prior_intent)
        if fallback is None:
            return {"status": "llm-unavailable", "kind": "knowledge", "knowledge_intent": intent,
                    "answer": "The local narrative engine is not available. " + str(exc)}
        fallback = dict(fallback)
        fallback["llm_error"] = str(exc)
        fallback["llm_provider"] = "Ollama"
        fallback["llm_local"] = True
        fallback["narrative_generated"] = False
        fallback["synthesis_mode"] = "deterministic-fallback"
        return fallback

    return {
        "status": "ok",
        "kind": "knowledge",
        "knowledge_intent": intent,
        "answer": answer,
        "knowledge_counts": k.get("counts", {}),
        "grounding": "Reunion Person Knowledge",
        "narrative_generated": True,
        "synthesis_mode": "local-llm-grounded",
        "llm_provider": "Ollama",
        "llm_model": model,
        "llm_local": True,
    }
