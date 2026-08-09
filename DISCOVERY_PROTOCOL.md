# Discovery Protocol

## Evidence states

- OBSERVED — directly measurable in the package or capture.
- CORRELATED — statistically associated with another observed feature.
- STRUCTURAL — repeatable grammar/boundary behaviour.
- CANDIDATE — proposed interpretation requiring additional evidence.
- VERIFIED — confirmed through controlled probes or independent decoding.

## Semantic naming rule

A structural Object Class must not receive a Reunion semantic name because its
payload merely looks suggestive. A semantic label requires controlled evidence
that adding, removing or changing the corresponding Reunion field changes the
predicted class or structure reproducibly.

## Stability rule

Build 11 Object Class IDs are SHA-1-derived identifiers of canonical structural
fingerprints and are deterministic for an unchanged fingerprint.

## Regression rule

Every Discovery release runs the entire project test suite and must not silently
replace production decoder semantics.

## Build 13 semantic probe rule

Semantic labels enter the system only as a declaration of the controlled edit
performed by the researcher. They are not inferred from Object Class payloads.
`VERIFIED` may be assigned automatically only after at least three consistent
controlled probes with no contradictions and >=95% evidence confidence.
`CANONICAL` is never assigned automatically.
