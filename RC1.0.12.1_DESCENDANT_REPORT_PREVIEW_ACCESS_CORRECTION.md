# FFD 2.0 RC1.0.12.1 — Descendant Report Preview Access Correction

RC1.0.12 created the standalone descendant renderer but did not expose a visible launch control on the normal Person > Publish screen.

This correction adds **Descendant Report — Preview (HTML)** beneath each family listed on Person > Publish and uses the existing `/publish/family/<id>/descendants` action.

Pass 1 remains fixed at four generations for visual review. No descendant traversal or report presentation changes are made.
