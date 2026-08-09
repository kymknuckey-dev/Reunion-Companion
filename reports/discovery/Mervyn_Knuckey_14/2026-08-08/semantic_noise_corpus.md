# Semantic Noise Suppression & Probe Corpus

```text
Semantic Probe Corpus Analysis
==============================
Probes                 9
ADD                    3
MODIFY                 5
COMPOUND               1
Raw spans              6,980
Suppressed noise       442
Semantic candidates    976
Unknown spans          5,562
Recurring patterns     45

Per Probe
---------
Probe                 Op        Raw   Semantic   Noise  Unknown  Decoded  Classes  Edges
birth-date           MODIFY     841        204      75      562        1        0      0
birth-place          MODIFY     960          6      52      902        0        0      0
birth-memo           MODIFY     823        746      77        0        0        2      2
occupation           ADD          1          0       0        1        0        0      0
education            ADD        904          0      38      866        0        0      0
religion             ADD       1359          9      42     1308        0        0      0
misc-note            MODIFY     624          6      49      569        0        0      0
research-note        COMPOUND   613          0      73      540        0        0      0
marriage             MODIFY     855          5      36      814        0        0      0

Most Recurrent Patterns
-----------------------
 88.9%  UI_ARCHIVE             occ=113   probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=50    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=22    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=20    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  DOCUMENT_PATH          occ=17    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  DOCUMENT_PATH          occ=16    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=15    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=14    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=14    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=13    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 88.9%  UI_ARCHIVE             occ=13    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=2578  probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=1213  probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=1066  probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=254   probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=139   probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=96    probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=87    probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=68    probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UNKNOWN                occ=23    probes=birth-date,birth-place,education,marriage,misc-note,religion,research-note
 77.8%  UI_ARCHIVE             occ=12    probes=birth-date,birth-memo,birth-place,marriage,misc-note,religion,research-note
 77.8%  DOCUMENT_PATH          occ=11    probes=birth-date,birth-memo,birth-place,education,misc-note,religion,research-note
 77.8%  DOCUMENT_PATH          occ=10    probes=birth-date,birth-memo,birth-place,education,marriage,misc-note,religion
 66.7%  UNKNOWN                occ=12    probes=birth-date,birth-place,education,marriage,misc-note,research-note
 66.7%  DOCUMENT_PATH          occ=10    probes=birth-memo,birth-place,education,marriage,misc-note,religion
 66.7%  DOCUMENT_PATH          occ=9     probes=birth-date,birth-memo,education,marriage,misc-note,religion
 66.7%  UI_ARCHIVE             occ=8     probes=birth-date,birth-memo,marriage,misc-note,religion,research-note
 66.7%  UI_ARCHIVE             occ=7     probes=birth-date,birth-memo,birth-place,misc-note,religion,research-note
 55.6%  TEXT_SEMANTIC_CANDIDATE occ=11    probes=birth-memo,birth-place,marriage,misc-note,religion
 55.6%  TEXT_SEMANTIC_CANDIDATE occ=10    probes=birth-memo,birth-place,marriage,misc-note,religion
```
