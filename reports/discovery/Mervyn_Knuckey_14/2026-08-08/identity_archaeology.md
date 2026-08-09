# Identity Archaeology — Build 22

```text
Identity Archaeology Engine
============================
Total regions               310
Unresolved regions          309
Regions with any identity   310
Regions with person_id      0
Regions with record_id      0
Regions with probe_id       310

Candidate Identity Keys
-----------------------
Score   Coverage  Grade                         Key
 98.4%   100.0%  STRONG_IDENTITY_CANDIDATE    probe_id
 50.0%     0.0%  ABSENT                       after_span
 50.0%     0.0%  ABSENT                       before_span
 50.0%     0.0%  ABSENT                       person_id
 50.0%     0.0%  ABSENT                       record_id

Verdict
-------
STOP
The accumulated pipeline does not retain enough owner/locality evidence to recover object instances reliably.
```

## Candidate identity keys

| Key | Score | Coverage | Exclusivity | Collision rate | Multi-region groups | Grade |
|---|---:|---:|---:|---:|---:|---|
| probe_id | 98.4% | 100.0% | 100.0% | 97.1% | 8 | STRONG_IDENTITY_CANDIDATE |
| after_span | 50.0% | 0.0% | 100.0% | 0.0% | 0 | ABSENT |
| before_span | 50.0% | 0.0% | 100.0% | 0.0% | 0 | ABSENT |
| person_id | 50.0% | 0.0% | 100.0% | 0.0% | 0 | ABSENT |
| record_id | 50.0% | 0.0% | 100.0% | 0.0% | 0 | ABSENT |

## Verdict

**STOP** — The accumulated pipeline does not retain enough owner/locality evidence to recover object instances reliably.

## Evidence boundary

Build 22 scores only identity/locality evidence already present in the Stage 16–21 pipeline. It does not infer hidden identifiers that are not represented in those artifacts.
