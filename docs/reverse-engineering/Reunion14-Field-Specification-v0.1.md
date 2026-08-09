# Reunion 14 Logical Field Specification — v0.1

Status: **Working reverse-engineering specification**

This document records what is currently known about the logical field model used by Reunion 14, based on:
- Reunion Field Settings screens supplied by the user.
- Reunion Field Usage Report for `Mervyn Knuckey 14.familyfile14`.
- Existing controlled Probe files and Reunion Companion decoder behaviour.

This is **not yet a binary file-format specification**. Binary offsets, record tags, link fields, and storage encodings are only recorded when independently verified.

---

## 1. Core logical model

Reunion exposes two major scopes:

### Person scope
- Events
- Facts
- Notes
- Flags

### Family scope
- Marriage fields
- Notes
- Events

These are logically distinct field classes and must remain distinct in Reunion Companion.

---

## 2. Person Events

Observed/default field types include:

- 1st Communion
- Adopted
- Baptism
- Baptism LDS
- Bar Mitzvah
- Bas Mitzvah
- Birth
- Blessing
- Burial
- Census
- Christen
- Citizenship
- Confirmation
- Confirmation LDS
- Cremation
- Death
- Emigration
- Employment
- Endowment
- Graduation
- Honors
- Immigration
- Initiatory LDS
- Land Purchase
- Misc Event (old)
- Naturalization
- Ordination
- Residence
- Retirement
- Seal to Parents

### Confirmed logical shape

Person Events may contain:
- event type
- date
- place
- memo

Field Settings also show per-event definition metadata:
- long abbreviation
- short date abbreviation
- short place abbreviation
- short memo abbreviation
- narrative arrangement
- narrative verb
- narrative place word
- GEDCOM tag
- export-as-EVEN option

### Current decoder status

Reunion Companion currently decodes:
- Birth
- Marriage (family/marriage scope)

Other event types remain to be decoded.

---

## 3. Person Facts

Observed/default fact types include:

- Alias/AKA
- Anc Interest Level
- Anst File#
- Cause of death
- Degree
- Desc Interest Level
- Description
- Education
- Eye color
- Hair color
- Height
- Hobbies
- Honors
- Married Name
- Namesake
- Nationality
- Occupation
- Race
- Reference #
- Religion
- Religious Name
- Skin color
- Soc. Sec. #
- Weight

Default Person Facts shown in Reunion:
- Occupation
- Education
- Religion

### Confirmed logical shape

Facts are text/value fields rather than timeline events.

Field Settings show:
- long abbreviation
- short abbreviation
- font
- GEDCOM tag

### Current decoder status

No Fact values are decoded into the Foundation model yet.

---

## 4. Person Notes

Observed note types include:

- Building achievements
- Education
- Medical
- Military
- Military Service
- Misc. Notes
- Monument Inscription
- New Note
- Research
- Resume
- Sport Achievement

Default Person Notes:
- Misc. Notes
- Research

### Confirmed logical shape

Notes are typed text blocks.

Field Settings show:
- abbreviation
- font
- GEDCOM tag

### Current decoder status

Controlled Probe notes are decoded, but the large Knuckey database currently yields zero decoded notes. The full-database note storage/linkage remains unresolved.

---

## 5. Person Flags

Observed flags include:

- Clergy
- Earliest Ancestor
- Military
- Private
- Research Complete
- Research doubt.

### Confirmed logical shape

Flags are boolean/presence-style fields.

Field Settings show:
- abbreviation
- narrative form
- exclude-from-reports option
- GEDCOM tag

### Current decoder status

No person flags are decoded into the Foundation model yet.

---

## 6. Marriage fields

Observed marriage field types:

- Annulment
- Civil Union
- Common Law
- Divorce
- Domestic Partnership
- Marriage
- Separation
- Unmarried

### Confirmed logical shape

Marriage fields may contain:
- type
- date
- place
- memo

Field Settings show:
- long abbreviation
- short date/place/memo abbreviations
- narrative arrangement
- narrative verb
- narrative place word
- GEDCOM tag

### Current decoder status

Marriage is partially decoded. Other marriage field types are not yet decoded.

---

## 7. Family Notes

Observed Family Notes:
- Misc. Notes
- Research

### Current decoder status

Not yet decoded in the full Knuckey database.

---

## 8. Family Events

Observed Family Events:
- Engagement
- Filed for Divorce
- Marriage License
- Sealing Spouse
- Separated

### Confirmed logical shape

Family Events use the same date/place/memo style as Person Events.

### Current decoder status

Not yet decoded.

---

## 9. Field Usage benchmark — Knuckey database

The Field Usage Report gives authoritative expected counts for the current database.

### Non-zero fields

| Name | Type | Reunion count |
|---|---|---:|
| Birth | Event | 5,422 |
| Death | Event | 1,946 |
| Misc. Notes | Note | 1,669 |
| Marriage | Marriage | 1,533 |
| Clergy | Flag | 994 |
| Christen | Event | 616 |
| Occupation | Fact | 456 |
| Burial | Event | 429 |
| Research | Note | 362 |
| Education | Fact | 100 |
| Religion | Fact | 89 |
| Military Service | Note | 86 |
| Divorce | Marriage | 47 |
| Cremation | Event | 46 |
| Common Law | Marriage | 20 |
| Medical | Note | 12 |
| Unmarried | Marriage | 6 |
| Building achievements | Note | 5 |
| Education (Note) | Note | 4 |
| Separation | Marriage | 4 |
| Domestic Partnership | Marriage | 3 |
| Military | Flag | 2 |
| Sport Achievement | Note | 2 |
| Misc. Notes (Family) | Family Note | 1 |
| Monument Inscription | Note | 1 |
| Research doubt. | Flag | 1 |
| Resume | Note | 1 |

### Zero-use fields

The following configured fields exist but have zero uses in the current database:

- 1st Communion (Event)
- Adopted (Event)
- Alias/AKA (Fact)
- Anc Interest Level (Fact)
- Annulment (Marriage)
- Anst File# (Fact)
- Baptism (Event)
- Baptism LDS (Event)
- Bar Mitzvah (Event)
- Bas Mitzvah (Event)
- Blessing (Event)
- Cause of death (Fact)
- Census (Event)
- Citizenship (Event)
- Civil Union (Marriage)
- Confirmation (Event)
- Confirmation LDS (Event)
- Degree (Fact)
- Desc Interest Level (Fact)
- Description (Fact)
- Earliest Ancestor (Flag)
- Emigration (Event)
- Employment (Event)
- Endowment (Event)
- Engagement (Family Event)
- Eye color (Fact)
- Filed for Divorce (Family Event)
- Graduation (Event)
- Hair color (Fact)
- Height (Fact)
- Hobbies (Fact)
- Honors (Event)
- Honors (Fact)
- Immigration (Event)
- Initiatory LDS (Event)
- Land Purchase (Event)
- Marriage License (Family Event)
- Married Name (Fact)
- Military (Note)
- Namesake (Fact)
- Nationality (Fact)
- Naturalization (Event)
- New Note (Note)
- Ordination (Event)
- Private (Flag)
- Race (Fact)
- Reference # (Fact)
- Religious Name (Fact)
- Research (Family Note)
- Research Complete (Flag)
- Residence (Event)
- Retirement (Event)
- Seal to Parents (Event)
- Sealing Spouse (Family Event)
- Separated (Family Event)
- Skin color (Fact)
- Soc. Sec. # (Fact)
- Weight (Fact)

---

## 10. Decoder acceptance targets

For each decoded field type, Reunion Companion should eventually report:

```text
decoded_count == Reunion Field Usage Report count
```

unless a documented Reunion reporting rule explains a difference.

Current benchmark examples:

| Field | Reunion | Companion Beta 2 | Coverage |
|---|---:|---:|---:|
| Birth | 5,422 | 5,185 | 95.6% |
| Marriage | 1,533 | 1,447 | 94.4% |
| Death | 1,946 | 0 | 0.0% |
| Christen | 616 | 0 | 0.0% |
| Burial | 429 | 0 | 0.0% |
| Cremation | 46 | 0 | 0.0% |
| Occupation | 456 | 0 | 0.0% |
| Misc. Notes | 1,669 | 0 | 0.0% |
| Research | 362 | 0 | 0.0% |

---

## 11. Binary specification status

### Verified
- Person IDs
- sex codes
- birth dates from controlled Reunion 14 records
- direct spouse IDs
- experimental child-family link using observed `0x003C`
- marriage dates from controlled family-event patterns
- event place IDs via length-prefixed `[[pt:n]]` tokens
- place resolution through `places.cache`
- standalone controlled-Probe person note records
- raw `0x0064` values are preserved but not yet interpreted

### Not yet specified
- general Person Event record layout
- Person Fact record layout
- Person Note linkage in large databases
- Person Flag storage
- Marriage subtype field identifiers
- Family Note storage
- Family Event storage
- citation linkage
- media filename/path linkage
- field-definition table storage
- custom field definitions

---

## 12. Reverse-engineering method from v0.1 onward

For every logical field class:

1. Use Reunion Field Usage Report to establish expected count.
2. Create or identify a controlled record with exactly one known field instance.
3. Save a before/after Reunion package if practical.
4. Compare binary/cache differences.
5. Identify stable record tags and link fields.
6. Add decoder code.
7. Add regression tests.
8. Re-run full Knuckey diagnostics.
9. Record decoded count vs Reunion expected count.
10. Update this specification only when evidence is verified.

---

## 13. Priority order

Recommended high-value order based on actual Knuckey usage:

1. Death — 1,946
2. Misc. Notes — 1,669
3. Clergy flag — 994
4. Christen — 616
5. Occupation — 456
6. Burial — 429
7. Research notes — 362
8. Education fact — 100
9. Religion fact — 89
10. Military Service note — 86
11. Divorce — 47
12. Cremation — 46

This order maximises useful decoded data while progressively revealing each field class.
