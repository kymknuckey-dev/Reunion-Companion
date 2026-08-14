# FFD 1.9 Build 2 — Grounded Person Narrative & Presentation Biography

## Principle
- **Research = evidence**: original Reunion notes are shown faithfully, including authored line and paragraph breaks.
- **Presentation = narrative**: Biography is generated from structured Reunion facts and original notes under strict grounding rules.
- **Publication = narrative for print**: the existing publication narrative remains a reader-facing derived representation.

## Narrative cache
Presentation biographies are cached locally by person, source-content fingerprint and narrative-engine version. Reopening an unchanged biography does not invoke the local LLM again. Changes to relevant imported notes/events change the fingerprint and cause regeneration on the next visit.

The cache is derived Companion data only. It never modifies imported Reunion notes.

## Presentation activity
When a Presentation Biography is not already cached, the page displays an activity spinner while the local narrative is prepared. Cached biographies return immediately.

## Layout refinements
Additional vertical spacing separates the selected-person heading/portrait from the navigation below and separates the Person Overview action-card row from the overview content.
