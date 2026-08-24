# FFD 2.0 RC1.0.13 — Navigation, Person Focus & Conversation UX Consolidation

## Scope

UI/interaction consolidation only.

### Left navigation
- Clarify section hierarchy and separators.
- Use a restrained active state with a left indicator rather than a heavy filled button.
- Label the current context as **Selected person**.
- Reorder person navigation to the normal reading flow:
  Overview, Timeline, Biography, Family Chart, Family, Media, Sources (Research mode), Ask about.
- Keep Publish and Reports grouped under Output.
- Give Home and Search their own active states.

### Person context
- The persistent person strip explicitly labels **Current person**.
- Preserve lifespan and immediate family context.
- No person-selection or genealogy behaviour changes.

### Conversation focus
- Compact the conversation-focus display into one focus bar.
- Show the active conversation person prominently.
- When focus differs from the conversation origin, show the origin unobtrusively.
- Keep **Move to <relative>** as an explicit choice; relatives do not automatically become focus.
- Keep **← Return to <origin>** available inline.
- Keep follow-up pronoun guidance small and secondary.

### Regression boundary
Do not change relationship resolution, ambiguity handling, pronoun/possessive semantics,
publishing, report generation, History Book scope, or genealogy.
