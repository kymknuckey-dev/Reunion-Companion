# Reunion Companion Inventory Update

Copy the contents of this update folder into your existing:

```text
~/Development/Reunion Companion
```

Allow Finder to merge folders and replace files.

Then run:

```bash
cd "$HOME/Development/Reunion Companion"
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Try the new command:

```bash
reunion-companion inventory "/Users/kymknuckey/Documents/Reunion Files/Probe-16.familyfile14"
reunion-companion inventory "/Users/kymknuckey/Documents/Reunion Files/Probe-16.familyfile14" --people
reunion-companion inventory "/Users/kymknuckey/Documents/Reunion Files/Probe-16.familyfile14" --people --files
reunion-companion inventory "/Users/kymknuckey/Documents/Reunion Files/Probe-16.familyfile14" --json
```
