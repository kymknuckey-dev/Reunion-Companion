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
