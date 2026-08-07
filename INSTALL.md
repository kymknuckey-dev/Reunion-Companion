# Foundation Layer v0.10.0-alpha3 — Install

Alpha 3 is cumulative and additive.

Merge:

```text
src/reunion_companion/foundation/
tests/test_foundation.py
tests/test_foundation_objects.py
tests/test_foundation_repository.py
tests/test_foundation_database.py
```

into your existing Reunion Companion project.

Do not replace or modify the established `model/`, decoder, engine, or CLI files.

Then run:

```bash
cd "$HOME/Development/Reunion Companion"
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Expected:

```text
82 passed
```

If the result differs, do not make manual fixes. Send the complete output back.
