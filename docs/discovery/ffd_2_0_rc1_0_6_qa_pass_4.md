# FFD 2.0 RC1.0.6 — Search & Identity Discovery, QA Pass 4

## Purpose
QA Pass 4 removes the remaining identity-discovery divergence between **Search the Family** and **Ask about the Family**.

## Governing rule
An explicit person name in a question is resolved through the same no-focus identity-discovery pipeline regardless of entry point. Existing conversation focus remains authoritative for pronouns and implicit follow-ups, but it must not prune, promote, or collapse candidates for an explicitly named person.

## Presentation consistency
Both entry points use equivalent identity lanes and ordering:

1. Best likely matches
2. People recorded with this name
3. Other family/name associations

Both retain the same candidate explanations and the same six-direct-result first-screen limit before **More people recorded with this name**.

## Focus behaviour
Selecting **Answer using this person →** answers using the selected canonical Reunion person. If Ask already has a conversation focus, the focus remains sticky and Companion may offer the existing explicit move-conversation action.

## Non-goals
This pass does not change QA Pass 3 ranking, add new name associations, infer unrecorded facts, or redesign navigation.
