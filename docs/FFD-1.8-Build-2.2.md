# FFD 1.8 Build 2.2 — Publishing Runtime Dependency Hardening

Build 2.2 closes a portability gap discovered during the clean M2 Pro deployment.

A Family Book PDF could be generated and opened directly, but its Companion web representation was incomplete until the MacBook virtual environment was given the same PDF/image runtime used on the development Mac. The missing packages were Pillow and PyMuPDF.

## Changes

- Declares `Pillow>=12.3.0` and `PyMuPDF>=1.28.2` as normal project dependencies in `pyproject.toml`.
- A clean `python -m pip install -e .` therefore installs the publishing runtime automatically.
- The portable-Mac bootstrap now verifies both Pillow and PyMuPDF and points an incomplete installation back to the project dependency install.
- Adds regression coverage that creates a two-page PDF and requires Companion's document renderer to produce a PyMuPDF preview for every page.

## Existing generated reports

Installing the missing runtime does not retroactively recreate preview assets produced earlier without it. If an existing PDF still has an incomplete Companion representation, delete/regenerate that report (or its generated preview assets) after installing Build 2.2. The underlying PDF may already be valid.

## Portability rule

Do not manually reproduce the development Mac's Python packages. Install Reunion Companion from its declared project dependencies. Publishing runtime requirements are now part of the project contract.
