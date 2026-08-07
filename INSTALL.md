# Foundation Layer v0.10.0-alpha5 — Install

Alpha 5 is cumulative and additive relative to the verified v0.9 application.

Merge:

```text
src/reunion_companion/foundation/
tests/test_foundation*.py
```

into your existing project.

Do not modify or replace the established `src/reunion_companion/model/`,
decoder, engine, publisher, or CLI files.

Then run:

```bash
cd "$HOME/Development/Reunion Companion"
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Expected:

```text
95 passed
```

If the result differs, stop and send the complete output back.
