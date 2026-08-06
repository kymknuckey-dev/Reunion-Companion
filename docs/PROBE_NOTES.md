# Probe Notes

## Confirmed

- Reunion 14 package detection
- Main data file: `familyfile.familydata`
- Separate given-name and surname fields
- Separate place catalogue and place-usage cache
- Birth and marriage events are stored as structured binary data
- Event memo text is length-prefixed
- Packed date day and month fields
- Person count grows independently of family count
- Adding a child updates an existing family

## Not yet proven

- Exact person-record boundaries
- Stable person ID decoding
- Exact spouse and child pointers
- Complete year decoding
- Date qualifier codes
- Source and citation structures
- Media ownership links


## Structured records milestone

- Person record envelope magic observed as `05 03 02 01`.
- Person record ID is decoded from the controlled record header.
- Sex field tag `0x001B`: `1 = male`, `2 = female`.
- Field tag `0x003C` is observed on Baby Probe with value `1` after assignment as a child of Family 1.
- Field tag `0x0064` is retained raw; its meaning is not yet assigned.
- Spouse membership is not yet directly decoded.
