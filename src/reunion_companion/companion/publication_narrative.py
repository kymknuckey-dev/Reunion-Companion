from __future__ import annotations
from .local_llm import OllamaClient, LocalLLMError


def preserve_note_layout(text: str | None) -> str:
    """Normalise line endings without collapsing authored paragraph structure."""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def publication_narrative(name: str, notes: list[str], facts: list[str], client=None) -> str:
    """Create reader-facing prose, grounded only in supplied Reunion evidence.

    If the local model is unavailable, preserve the authored notes rather than
    degrading publication or inventing a substitute.
    """
    source_notes=[preserve_note_layout(x) for x in notes if preserve_note_layout(x)]
    if not source_notes:
        return ""
    evidence="\n\n".join(source_notes)
    fact_text="\n".join(f"- {x}" for x in facts if x)
    prompt=f'''Write restrained family-history publication prose about {name}.\n\nSTRICT RULES:\n- Use ONLY facts present in EVIDENCE and STRUCTURED FACTS below.\n- Do not infer, embellish, add dates, places, relationships, motives or achievements.\n- Preserve names, dates and factual claims accurately.\n- Improve grammar, paragraphing and flow; remove obvious repetition.\n- Return publication prose only, with paragraphs separated by blank lines.\n\nSTRUCTURED FACTS:\n{fact_text or "(none)"}\n\nEVIDENCE — ORIGINAL REUNION NOTES:\n{evidence}\n'''
    try:
        return (client or OllamaClient()).generate(prompt).strip()
    except LocalLLMError:
        return evidence
