# Object Reconstruction — Build 20

```text
Object Reconstruction Engine
============================
Objects reconstructed        7
Object relations             12
Region memberships           310
Shared region memberships    0
Unknown region memberships   0
Verified object candidates   0
High-confidence objects      0
Object candidates            7

Object types are evidence-backed hypotheses, not claims about Reunion's private implementation.
```

## Objects

| Object | Type | Confidence | Completeness | Status | Members |
|---|---|---:|---:|---|---:|
| RO-73EEB1FCA9 | Birth Event | 83.0% | 100.0% | OBJECT_CANDIDATE | 123 |
| RO-5EA1F83D38 | Occupation | 75.5% | 100.0% | OBJECT_CANDIDATE | 1 |
| RO-F14F348E87 | Research Notes | 75.4% | 100.0% | OBJECT_CANDIDATE | 24 |
| RO-6D4CB63E0E | Marriage Event | 74.0% | 100.0% | OBJECT_CANDIDATE | 36 |
| RO-47AC8792C6 | Misc Notes | 73.8% | 100.0% | OBJECT_CANDIDATE | 35 |
| RO-AAF87FE57A | Education | 73.3% | 100.0% | OBJECT_CANDIDATE | 43 |
| RO-B04D58C69D | Religion | 72.8% | 100.0% | OBJECT_CANDIDATE | 48 |

## Relations

| Relation | Source | Target | Type | Confidence |
|---|---|---|---|---:|
| OR-111D3EFD6D | RO-73EEB1FCA9 | RO-47AC8792C6 | SEMANTIC_ASSOCIATION | 45.0% |
| OR-4C27A1926E | RO-47AC8792C6 | RO-B04D58C69D | SEMANTIC_ASSOCIATION | 44.2% |
| OR-E995D60E2A | RO-6D4CB63E0E | RO-47AC8792C6 | SEMANTIC_ASSOCIATION | 43.9% |
| OR-28A2CA4EDD | RO-73EEB1FCA9 | RO-B04D58C69D | SEMANTIC_ASSOCIATION | 43.9% |
| OR-2929A08197 | RO-6D4CB63E0E | RO-B04D58C69D | SEMANTIC_ASSOCIATION | 43.8% |
| OR-28CE8DFB09 | RO-73EEB1FCA9 | RO-6D4CB63E0E | SEMANTIC_ASSOCIATION | 43.8% |
| OR-9656CD3EBC | RO-73EEB1FCA9 | RO-47AC8792C6 | ARCHITECTURAL_ASSOCIATION | 1.2% |
| OR-18C812A93B | RO-47AC8792C6 | RO-B04D58C69D | ARCHITECTURAL_ASSOCIATION | 1.1% |
| OR-387F447298 | RO-73EEB1FCA9 | RO-B04D58C69D | ARCHITECTURAL_ASSOCIATION | 0.9% |
| OR-3459A567C4 | RO-6D4CB63E0E | RO-47AC8792C6 | ARCHITECTURAL_ASSOCIATION | 0.9% |
| OR-0AEF5567FB | RO-73EEB1FCA9 | RO-6D4CB63E0E | ARCHITECTURAL_ASSOCIATION | 0.7% |
| OR-FDA2F72154 | RO-6D4CB63E0E | RO-B04D58C69D | ARCHITECTURAL_ASSOCIATION | 0.7% |

## Evidence boundary

Build 20 reconstructs logical objects from accumulated semantic evidence. It does not prove internal class names, storage ownership, pointer direction, or write semantics.
