# FFD 2.0 RC1.0.9 — Layout Correction

This correction is based on Git checkpoint `4e38193`. It leaves Reunion media import, preferred-photo semantics, marriage-document handling, and document classification unchanged.

The Family History Book photo-pair renderer now uses a full-width flex column for each half-page photo/caption unit. The image is centered within the printable width with `object-fit: contain`, captions remain fully visible directly beneath the image, portrait/square images use a caption-safe 106 mm maximum height, and the previously successful landscape maximum of 91 mm is retained.
