#!/usr/bin/env python3
import subprocess
files=["tests/test_ffd_1_9_build4_deterministic_family_grounding.py","tests/test_ffd_1_9_build4_0_1_relationship_aware_family_coverage.py"]
r=subprocess.run(["python","-m","pytest","-q"]+files)
print("\nFFD 1.9 Build 4.0.1 verification "+("PASSED." if r.returncode==0 else "FAILED."))
raise SystemExit(r.returncode)
