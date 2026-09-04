FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.3.1 — Release Metadata Forward-Compatibility Correction

Corrects the RC1.0.14.8.9.9.4.1.3.12.2.1 metadata regression test so it validates the live build/DMG release identities remain synchronized and structurally valid without permanently pinning them to the historical .12.2.1 release string.

The historical .12.2.1 identity remains preserved in build_app.py and package_dmg.py. The Ryerson evidence deduplication behavior introduced in .12.3 is unchanged.
