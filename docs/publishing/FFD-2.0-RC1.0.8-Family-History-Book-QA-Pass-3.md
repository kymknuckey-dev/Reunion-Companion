# FFD 2.0 RC1.0.8 — Family History Book QA Pass 3

## Scope

Marriage media in Reunion is family/marriage data. This pass makes the publication model preserve that attachment context. A document attached through `family_media` is eligible for Marriage Documents even when its title, attachment label, or filename is only the generic `Certificate`.

## Behaviour

- Read marriage media through `families -> family_media -> media`.
- Treat family-attached PDF/document images as marriage documents without requiring marriage wording in their metadata.
- Continue recognising explicitly named marriage/wedding documents from other attachment paths.
- Stable de-duplication prevents a media item linked through both family and person paths from appearing twice.
- Existing fitted document rendering is unchanged.
- All accepted Pass 2 Life & Biography and biography-hardening behaviour is frozen.
