#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
tests=[
 repo/"tests/test_ffd_2_0_build1_macos_application_foundation.py",
 repo/"tests/test_ffd_2_0_build2_native_companion_window.py",
 repo/"tests/test_ffd_2_0_build3_native_application_integration.py",
]
r=subprocess.run([sys.executable,"-m","pytest","-q",*[str(x) for x in tests]],cwd=repo)
if r.returncode: raise SystemExit(r.returncode)
r=subprocess.run([sys.executable,str(repo/"macos_app/build_app.py"),"--plan"],cwd=repo)
if r.returncode: raise SystemExit(r.returncode)
print("\nFFD 2.0 Build 3 verification PASSED.")
