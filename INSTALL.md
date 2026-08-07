# Foundation Layer v0.10.0-alpha2 — Install

Alpha 2 is cumulative and additive.

## Merge, do not overwrite the application

Merge:

```text
src/reunion_companion/foundation/
tests/test_foundation.py
tests/test_foundation_objects.py
```

into your existing Reunion Companion project.

Do **not** replace or modify:

```text
src/reunion_companion/model/
src/reunion_companion/media.py
src/reunion_companion/models.py
src/reunion_companion/domain.py
src/reunion_companion/event_engine.py
```

Then run:

```bash
cd "$HOME/Development/Reunion Companion"
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Expected result:

```text
74 passed
```

If you get anything other than 74 passed, do not make manual fixes. Send the
full test output back.
