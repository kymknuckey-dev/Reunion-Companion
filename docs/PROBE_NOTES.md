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


## Event milestone

- Packed year is `((value >> 10) & 0x07FF) + 192`.
- Bits above bit 20 are retained as unresolved high flags.
- Qualifier byte `0xA0` is observed for `abt`; exact dates use `0x00`.
- Person event field `0x03E8` contains the controlled Birth event.
- Family tags `0x0050` and `0x0051` contain direct spouse person IDs.
- The controlled family record contains the Marriage date `3 Mar 1950`.
- Event-to-place pointers are not yet decoded.
