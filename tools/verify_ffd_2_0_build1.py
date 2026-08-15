#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
checks=[
    ("Application foundation regression",
     [sys.executable,"-m","pytest","-q",str(repo/"tests/test_ffd_2_0_build1_macos_application_foundation.py")]),
    ("Application build plan",
     [sys.executable,str(repo/"macos_app/build_app.py"),"--plan"]),
]
ok=True
for label,cmd in checks:
    r=subprocess.run(cmd,cwd=repo)
    print(("✓" if r.returncode==0 else "✗"),label)
    ok &= r.returncode==0
print("\nFFD 2.0 Build 1 verification "+("PASSED." if ok else "FAILED."))
raise SystemExit(0 if ok else 1)
