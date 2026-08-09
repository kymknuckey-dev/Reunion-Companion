# Build 17 Installation

```bash
python tools/apply_build17.py "$HOME/Development/Reunion Companion"
cd "$HOME/Development/Reunion Companion"
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Restart Discovery, then run:

```text
architecture-summary "/path/PROBE_CORPUS_KNUCKEY.json"
architecture-components "/path/PROBE_CORPUS_KNUCKEY.json"
architecture-probe birth-date "/path/PROBE_CORPUS_KNUCKEY.json"
pipeline-build "/path/PROBE_CORPUS_KNUCKEY.json"
architecture-report "/path/PROBE_CORPUS_KNUCKEY.json"
```

Please return:
- `database_architecture.md`
- `architecture_snapshot.json`

Keep these locally:
- `pipeline/stage-16-canonical-regions.json`
- `pipeline/stage-17-architecture.json`

They become persistent inputs for later builds.
