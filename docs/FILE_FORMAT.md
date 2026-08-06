# Reunion File Format Notes

This document records only observations supported by controlled probe files.

## Reunion 14 package

Known main data filename:

```text
familyfile.familydata
```

Known supporting files may include:

```text
places.cache
placeUsage.cache
timestamps.cache
bookmarks.cache
surnames.cache
fmnames.cache
thumbnails/
```

## Confirmed observations

- Person names are stored as distinct fields.
- Places are catalogued separately and have usage indexing.
- Event memos can appear as length-prefixed UTF-8 text.
- Dates use a four-byte little-endian packed representation.
- A Reunion family file must be treated as proprietary and read-only.

## Packed date

Current working interpretation:

```text
bits 0–5   day
bits 6–9   month
bits 10+   year code and/or higher metadata
```

Missing day or month is represented as zero.

The exact year offset and qualifier encoding remain under investigation.
