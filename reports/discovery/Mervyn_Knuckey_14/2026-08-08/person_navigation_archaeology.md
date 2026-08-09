# Person Index & Navigation Archaeology — Build 23

```text
Person Index & Navigation Archaeology Engine
===========================================
Package files scanned        25
Person-ID byte hits          6,180
Person-index candidates      556
Controlled snapshot deltas   3
Change-log file candidates   12

Top Person Index candidates
---------------------------
Score   Encoding  Stride  Offset      IDs        File
 89.0%  u8            1     60,423  1,2,3      familyfile.familydata
 89.0%  u8           32     63,139  1,2,3      familyfile.familydata
 89.0%  u16le        32     63,139  1,2,3      familyfile.familydata
 89.0%  u8           32     65,280  1,2,3      familyfile.familydata
 89.0%  u16le        32     65,280  1,2,3      familyfile.familydata
 89.0%  u8            1     68,010  1,2,3      familyfile.familydata
 89.0%  u16be         2     69,589  1,2,3      familyfile.familydata
 89.0%  u16le         2     69,590  1,2,3      familyfile.familydata
 89.0%  u8            1        185  1,2,3      thumbnails/thumbnails_large/p1-8f4821-1000.jpg
 89.0%  u8            1        217  1,2,3      thumbnails/thumbnails_large/p1-8f4821-1000.jpg
 89.0%  u8            1        401  1,2,3      thumbnails/thumbnails_large/p1-8f4821-1000.jpg
 89.0%  u8            1        434  1,2,3      thumbnails/thumbnails_large/p1-8f4821-1000.jpg
 89.0%  u8            1        185  1,2,3      thumbnails/thumbnails_large/p2-90226f-1000.jpg
 89.0%  u8            1        217  1,2,3      thumbnails/thumbnails_large/p2-90226f-1000.jpg
 89.0%  u8            1        401  1,2,3      thumbnails/thumbnails_large/p2-90226f-1000.jpg
 89.0%  u8            1        434  1,2,3      thumbnails/thumbnails_large/p2-90226f-1000.jpg
 89.0%  u8            1        185  1,2,3      thumbnails/thumbnails_small/p1-8f4821-200.jpg
 89.0%  u8            1        217  1,2,3      thumbnails/thumbnails_small/p1-8f4821-200.jpg
 89.0%  u8            1        401  1,2,3      thumbnails/thumbnails_small/p1-8f4821-200.jpg
 89.0%  u8            1        434  1,2,3      thumbnails/thumbnails_small/p1-8f4821-200.jpg

Candidate Change Log files
--------------------------
  familyfile.familydata
  globalRecords.cache
  index.cache
  timestamps.cache
  bookmarks.cache
  find.cache
  phash.cache
  placeUsage.cache
  places.cache
  pstats.cache
  shGeneral.cache
  shNames.cache

Verdict
-------
PARTIAL
Navigation/index evidence exists, but the Person-ID-to-record path is not yet fully demonstrated.
```

## Index candidates

| Score | File | Encoding | Stride | Offset | IDs |
|---:|---|---|---:|---:|---|
| 89.0% | familyfile.familydata | u8 | 1 | 60423 | 1, 2, 3 |
| 89.0% | familyfile.familydata | u8 | 32 | 63139 | 1, 2, 3 |
| 89.0% | familyfile.familydata | u16le | 32 | 63139 | 1, 2, 3 |
| 89.0% | familyfile.familydata | u8 | 32 | 65280 | 1, 2, 3 |
| 89.0% | familyfile.familydata | u16le | 32 | 65280 | 1, 2, 3 |
| 89.0% | familyfile.familydata | u8 | 1 | 68010 | 1, 2, 3 |
| 89.0% | familyfile.familydata | u16be | 2 | 69589 | 1, 2, 3 |
| 89.0% | familyfile.familydata | u16le | 2 | 69590 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 1 | 185 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 1 | 217 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 1 | 401 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 1 | 434 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 1 | 185 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 1 | 217 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 1 | 401 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 1 | 434 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u8 | 1 | 185 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u8 | 1 | 217 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u8 | 1 | 401 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u8 | 1 | 434 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u8 | 1 | 185 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u8 | 1 | 217 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u8 | 1 | 401 | 1, 2, 3 |
| 89.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u8 | 1 | 434 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 29139 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 24 | 30042 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u16le | 24 | 30042 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 2 | 69590 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73335 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73337 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73339 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73341 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73343 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73345 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73347 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73349 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73351 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73353 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73355 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73357 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73359 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73361 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73363 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73365 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 48 | 73367 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73367 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 48 | 73369 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 64 | 73369 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 2 | 73884 | 1, 2, 3 |
| 81.0% | familyfile.familydata | u8 | 2 | 74074 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u16le | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 3 | 154 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 2 | 744 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u16le | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 3 | 154 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 2 | 744 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u8 | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u16le | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u8 | 3 | 154 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p1-8f4821-200.jpg | u8 | 2 | 744 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u8 | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u16le | 12 | 47 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u8 | 3 | 154 | 1, 2, 3 |
| 81.0% | thumbnails/thumbnails_small/p2-90226f-200.jpg | u8 | 2 | 744 | 1, 2, 3 |
| 77.0% | familyfile.familydata | u8 | 32 | 13887 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 21956 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 21970 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 16 | 29285 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 29286 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 16 | 29286 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 16 | 29286 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 32 | 30039 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 32 | 30041 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 30042 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 32 | 30042 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 16 | 30049 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 30050 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 16 | 30050 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 47778 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 47950 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 48002 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 16 | 55079 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 32 | 55079 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 55080 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 55080 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 16 | 55080 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 32 | 55080 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 16 | 55080 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 32 | 55080 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 4 | 55097 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 4 | 55100 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 4 | 55105 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 4 | 55108 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 4 | 55113 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 4 | 55116 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 4 | 55121 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 4 | 55124 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 8 | 58613 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 58614 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 8 | 58614 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 8 | 58615 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 58616 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 8 | 58616 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 32 | 61109 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 32 | 61111 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 61112 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 32 | 61112 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 4 | 61140 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 32 | 61237 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 32 | 61239 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 61240 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 32 | 61240 | 1, 2 |
| 77.0% | familyfile.familydata | u32le | 4 | 61268 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 63170 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 63342 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 63442 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 63947 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 32 | 63947 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 65311 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 65483 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 65583 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 66036 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 32 | 66036 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 32 | 66613 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 32 | 66615 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 66616 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 32 | 66616 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 67512 | 1, 2 |
| 77.0% | familyfile.familydata | u16le | 8 | 67512 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 67519 | 1, 2 |
| 77.0% | familyfile.familydata | u32be | 16 | 67637 | 1, 2 |
| 77.0% | familyfile.familydata | u16be | 16 | 67639 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 67640 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 69854 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 69856 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 69858 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 69860 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 69862 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 69870 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 69872 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 69874 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 69876 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 69878 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 69878 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 69880 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 69882 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 69884 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 71603 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73339 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73341 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73343 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73345 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73347 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73349 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73351 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73353 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73355 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73355 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73357 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73357 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73359 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73359 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73361 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73361 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 73363 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73363 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73363 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 73365 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73365 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73365 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 73367 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73367 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73367 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 8 | 73369 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 16 | 73369 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 32 | 73369 | 1, 2 |
| 77.0% | familyfile.familydata | u8 | 1 | 74456 | 1, 2 |
| 77.0% | placeUsage.cache | u32be | 16 | 33 | 1, 2 |
| 77.0% | placeUsage.cache | u16be | 16 | 35 | 1, 2 |
| 77.0% | placeUsage.cache | u8 | 16 | 36 | 1, 2 |
| 77.0% | placeUsage.cache | u16le | 16 | 36 | 1, 2 |
| 77.0% | placeUsage.cache | u32le | 16 | 36 | 1, 2 |
| 77.0% | placeUsage.cache | u32be | 4 | 45 | 1, 2 |
| 77.0% | placeUsage.cache | u32le | 4 | 48 | 1, 2 |
| 77.0% | places.cache | u8 | 8 | 28 | 1, 2 |
| 77.0% | places.cache | u16le | 8 | 28 | 1, 2 |
| 77.0% | places.cache | u32le | 8 | 28 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 8 | 149 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 32 | 154 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 32 | 174 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 16 | 386 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 32 | 386 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 32 | 388 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 8 | 394 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 1 | 419 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 16 | 419 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p1-8f4821-1000.jpg | u8 | 1 | 430 | 1, 2 |
| 77.0% | thumbnails/thumbnails_large/p2-90226f-1000.jpg | u8 | 32 | 154 | 1, 2 |

## Controlled deltas

### Probe-22

```text
Navigation Delta — Probe-22
===========================
Changed Person ID -
Changed field     -
Changed files     9

Changed runs
------------
File | Start | BeforeLen | AfterLen | Nearby Person IDs
bookmarks.cache | 17 | 3 | 3 | 3
familyfile.familydata | 16 | 23 | 23 | 1,2,3
familyfile.familydata | 72 | 7 | 7 | 1,2,3
familyfile.familydata | 122 | 11 | 11 | 1,2,3
familyfile.familydata | 328 | 2 | 2 | 1,2,3
familyfile.familydata | 348 | 4 | 4 | 1,2,3
familyfile.familydata | 399 | 1 | 1 | 1,2,3
familyfile.familydata | 418 | 1 | 1 | 2,3
familyfile.familydata | 24,634 | 74 | 74 | 1,2,3
familyfile.familydata | 28,860 | 1 | 1 | 1,2,3
familyfile.familydata | 29,372 | 19 | 19 | 1,2,3
familyfile.familydata | 29,441 | 36 | 36 | 1,2,3
familyfile.familydata | 48,568 | 926 | 926 | 1,2,3
familyfile.familydata | 49,592 | 283 | 283 | 1,2,3
familyfile.familydata | 49,976 | 72 | 72 | 1,2,3
familyfile.familydata | 50,104 | 67 | 67 | 1,2,3
familyfile.familydata | 50,232 | 38 | 38 | 1,2,3
familyfile.familydata | 50,360 | 199 | 199 | 1,2,3
familyfile.familydata | 50,586 | 1 | 1 | 1,2,3
familyfile.familydata | 50,616 | 34 | 34 | 1,2,3
familyfile.familydata | 50,692 | 15 | 15 | 1,2,3
familyfile.familydata | 50,736 | 3 | 3 | 1,3
familyfile.familydata | 51,896 | 2824 | 2824 | 1,2,3
familyfile.familydata | 54,840 | 30 | 30 | 1,2,3
familyfile.familydata | 54,900 | 40 | 40 | 1,2,3
familyfile.familydata | 55,000 | 10 | 10 | 1,2
familyfile.familydata | 55,040 | 2 | 2 | 1,2
familyfile.familydata | 55,060 | 88 | 88 | 1,2,3
familyfile.familydata | 55,216 | 2840 | 2840 | 1,2,3
familyfile.familydata | 60,858 | 175 | 175 | 1,2,3
familyfile.familydata | 61,092 | 1 | 1 | 1,2,3
familyfile.familydata | 61,112 | 170 | 170 | 1,2,3
familyfile.familydata | 61,370 | 118 | 118 | 1,2,3
familyfile.familydata | 62,396 | 1 | 1 | 1,2,3
familyfile.familydata | 64,060 | 1 | 1 | 1,2,3
familyfile.familydata | 66,232 | 294 | 294 | 1,2,3
familyfile.familydata | 66,616 | 88 | 88 | 1,2,3
familyfile.familydata | 66,746 | 50 | 50 | 1,2,3
familyfile.familydata | 66,840 | 26 | 26 | 1,2,3
familyfile.familydata | 68,800 | 68 | 68 | 1,2,3
familyfile.familydata | 74,424 | 2176 | 0 | 1,2,3
find.cache | 0 | 12 | 0 | -
index.cache | 0 | 60 | 0 | 1,2,3
phash.cache | 0 | 120 | 0 | 1,2,3
pstats.cache | 0 | 64 | 0 | 1,2,3
shGeneral.cache | 0 | 32 | 0 | -
shNames.cache | 0 | 59 | 0 | 2
timestamps.cache | 0 | 9 | 9 | 1,2,3
timestamps.cache | 716 | 0 | 20 | 1,2
```

### Probe-23

```text
Navigation Delta — Probe-23
===========================
Changed Person ID -
Changed field     -
Changed files     4

Changed runs
------------
File | Start | BeforeLen | AfterLen | Nearby Person IDs
familyfile.familydata | 36 | 2 | 2 | 1,2,3
familyfile.familydata | 72 | 6 | 6 | 1,2,3
familyfile.familydata | 124 | 9 | 9 | 1,2,3
familyfile.familydata | 28,860 | 14 | 14 | 1,2,3
familyfile.familydata | 28,902 | 21 | 21 | 1,2,3
familyfile.familydata | 28,984 | 2 | 2 | 1,2
familyfile.familydata | 29,372 | 19 | 19 | 1,2,3
familyfile.familydata | 29,436 | 52 | 52 | 1,2,3
familyfile.familydata | 53,560 | 263 | 263 | 1,2,3
familyfile.familydata | 53,858 | 1 | 1 | 1,2
familyfile.familydata | 53,886 | 1 | 1 | 1,2
familyfile.familydata | 53,914 | 1 | 1 | -
familyfile.familydata | 60,856 | 128 | 128 | 1,2,3
familyfile.familydata | 61,370 | 118 | 118 | 1,2,3
familyfile.familydata | 62,392 | 1532 | 1532 | 1,2,3
familyfile.familydata | 64,704 | 13 | 13 | 1,2,3
familyfile.familydata | 64,743 | 1 | 1 | 1,2,3
familyfile.familydata | 66,130 | 81 | 81 | 1,2,3
familyfile.familydata | 66,236 | 1 | 1 | 1,2,3
placeUsage.cache | 0 | 68 | 0 | 1,2
places.cache | 0 | 105 | 0 | 1,2
timestamps.cache | 0 | 9 | 9 | 1,2,3
timestamps.cache | 736 | 0 | 20 | 1,2
```

### Probe-24

```text
Navigation Delta — Probe-24
===========================
Changed Person ID -
Changed field     -
Changed files     3

Changed runs
------------
File | Start | BeforeLen | AfterLen | Nearby Person IDs
familyfile.familydata | 36 | 2 | 2 | 1,2,3
familyfile.familydata | 72 | 6 | 6 | 1,2,3
familyfile.familydata | 124 | 9 | 9 | 1,2,3
familyfile.familydata | 28,858 | 182 | 182 | 1,2,3
familyfile.familydata | 29,370 | 118 | 118 | 1,2,3
familyfile.familydata | 30,264 | 248 | 248 | 1,2,3
familyfile.familydata | 30,656 | 76 | 76 | 1,2,3
familyfile.familydata | 51,896 | 21 | 21 | 1,2,3
familyfile.familydata | 53,506 | 363 | 363 | 1,2,3
familyfile.familydata | 53,894 | 33 | 33 | 1,2,3
familyfile.familydata | 53,950 | 1 | 1 | 1,2,3
familyfile.familydata | 53,978 | 1213 | 1213 | 1,2,3
familyfile.familydata | 60,856 | 130 | 130 | 1,2,3
familyfile.familydata | 61,019 | 45 | 45 | 1,2,3
familyfile.familydata | 62,392 | 22 | 22 | 1,2,3
familyfile.familydata | 62,439 | 1 | 1 | 1,2,3
familyfile.familydata | 63,826 | 5 | 5 | 1,2,3
familyfile.familydata | 63,848 | 148 | 148 | 1,2,3
familyfile.familydata | 64,700 | 1 | 1 | 1,2,3
familyfile.familydata | 66,236 | 13 | 13 | 1,2,3
familyfile.familydata | 66,455 | 1 | 1 | -
familyfile.familydata | 66,616 | 102 | 102 | 1,2,3
familyfile.familydata | 66,746 | 62 | 62 | 1,2,3
familyfile.familydata | 66,840 | 26 | 26 | 1,2,3
familyfile.familydata | 68,794 | 51 | 51 | 1,2,3
familyfile.familydata | 74,424 | 0 | 1792 | 1,2,3
globalRecords.cache | 0 | 20 | 0 | 1
timestamps.cache | 0 | 9 | 9 | 1,2,3
timestamps.cache | 756 | 0 | 20 | 1,2
```

## Candidate Change Log files

- `familyfile.familydata`
- `globalRecords.cache`
- `index.cache`
- `timestamps.cache`
- `bookmarks.cache`
- `find.cache`
- `phash.cache`
- `placeUsage.cache`
- `places.cache`
- `pstats.cache`
- `shGeneral.cache`
- `shNames.cache`

## Verdict

**PARTIAL** — Navigation/index evidence exists, but the Person-ID-to-record path is not yet fully demonstrated.

## Evidence boundary

A Person-ID byte hit or ordered sequence is a navigation/index candidate only. Build 23 does not label a structure as Reunion's Person Index until controlled edits corroborate it.
