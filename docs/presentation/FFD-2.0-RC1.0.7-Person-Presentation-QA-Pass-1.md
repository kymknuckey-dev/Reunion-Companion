# FFD 2.0 RC1.0.7 — Person Presentation QA Pass 1

## Purpose
Make the selected person's Overview feel like a family-history page rather than an application dashboard.

## Changes
- Use one editorial identity hero on the Presentation Overview, avoiding a duplicate compact identity strip.
- Enlarge and integrate the person's portrait.
- Surface recorded parents/spouse context without inferring unrecorded facts.
- Replace database-count fallbacks in Life at a Glance with recorded human facts only.
- Present dated life events chronologically, with stable handling for undated facts.
- Make family names themselves the navigation targets and remove repetitive View person links.
- Show Media & Documents only when image previews are actually available.
- Keep sparse people deliberate by omitting unsupported glance/media content rather than leaving artificial placeholders.

## Non-goals
No changes to Navigation QA Pass 1 architecture, Search & Identity Discovery, relationships, GEDCOM handling, genealogy assembly, or publishing internals.
