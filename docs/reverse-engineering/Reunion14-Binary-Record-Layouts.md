# Reunion 14 Binary Record Layouts — Working Notes

This document is intentionally sparse. Only verified binary structures belong here.

## Person
### Verified
- Person record ID: verified by controlled probes.
- Sex code: verified by controlled probes.
- Birth date: verified by controlled probes.
- Direct spouse ID linkage: verified by controlled probes.

### Candidate / experimental
- `0x003C`: observed child-to-family linkage; requires more family-shape confirmation.
- `0x0064`: raw values preserved; meaning unknown.

## Events
### Birth
- Date decoding verified from controlled probes.
- Place ID can be exposed through length-prefixed `[[pt:n]]` token.

### Death
- Not yet specified.

### Burial
- Not yet specified.

### Christen
- Not yet specified.

### Cremation
- Not yet specified.

## Facts
- Record layout not yet specified.

## Notes
- Standalone controlled-Probe person note record is decoded.
- General full-database note linkage not yet specified.

## Flags
- Storage not yet specified.

## Marriage fields
- Marriage date pattern decoded from controlled probes.
- Other marriage subtypes not yet specified.

## Family events
- Not yet specified.

## Sources / citations
- Source records discovered.
- Citation linkage not yet specified.

## Media
- Attachment records discovered.
- Filename/path linkage not yet specified.

## Field definitions
- Reunion UI confirms configurable field-definition metadata exists logically.
- Binary storage of field definitions is not yet located.
