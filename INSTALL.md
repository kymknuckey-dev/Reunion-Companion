# Foundation Layer v0.10.0-alpha4 — Install

Alpha 4 is cumulative and remains additive relative to the working v0.9 application.

Merge:

```text
src/reunion_companion/foundation/
tests/test_foundation*.py
```

into your existing Reunion Companion project.

Do not modify or replace the established `model/`, decoder, engine, publisher,
or CLI files.

Then run:

```bash
cd "$HOME/Development/Reunion Companion"
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Expected:

```text
89 passed
```

If the result differs, do not make manual fixes. Send the complete output back.
