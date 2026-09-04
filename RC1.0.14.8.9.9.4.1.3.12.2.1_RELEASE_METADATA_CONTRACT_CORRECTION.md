# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.2.1 — Release Metadata Contract Correction

Corrects the remaining stale metadata regression contract from RC1.0.14.8.9.9.4.1.3.12.1.1.

That historical test incorrectly froze the then-current release identity as a permanent requirement. It now verifies the durable packaging invariant instead: build_app.py and package_dmg.py must expose the same live APP_RELEASE.

No Ryerson crawler or Manage-page behaviour changes are included.
