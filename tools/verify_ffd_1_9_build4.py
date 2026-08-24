#!/usr/bin/env python3
import subprocess
checks=[
 ["python","-m","pytest","-q","tests/test_ffd_1_9_build4_deterministic_family_grounding.py"],
 ["python","-m","pytest","-q","tests/test_ffd_1_8_build2_3_1_centralised_version_identity.py"],
]
ok=True
for cmd in checks:
 r=subprocess.run(cmd); ok &= r.returncode==0
print("\nFFD 1.9 Build 4 verification "+("PASSED." if ok else "FAILED."))
raise SystemExit(0 if ok else 1)
