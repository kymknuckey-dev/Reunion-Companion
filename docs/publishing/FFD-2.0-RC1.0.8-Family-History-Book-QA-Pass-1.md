# FFD 2.0 RC1.0.8 — Family History Book QA Pass 1

## Scope

- Extend the proven Birth Documents fitted-page model to Death & Burial Documents, Other Documents, and first PDF Marriage Documents so a heading is not stranded from its certificate.
- Recognise image-based marriage/wedding certificates as family marriage documents as well as PDF certificates.
- Make book publication self-sufficient: if a canonical stored Biography does not exist for an included person, generate and cache it during publication.
- Exclude Reunion/GEDCOM Changed/CHAN administrative metadata from biography evidence.
- For facts-only people, use deterministic grounded prose rather than asking the LLM to invent narrative transitions. This prevents unsupported statements such as “changed something” or “changed his religious affiliation”.
- Enrich each printed Individual Overview with Dad-style compact key facts: birth, occupation, education, religion, parents, spouse, children and death where recorded.

## Deferred

**Incoming Spouse Family Context** remains a later book-architecture requirement. When a spouse enters the principal descendant line, a later pass may introduce that spouse’s parents and relevant family/descendant context without repeating the already-established principal-line parents.
