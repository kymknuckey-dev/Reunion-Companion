#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
r=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve(); x=subprocess.run([sys.executable,"-m","pytest","-q",str(r/"tests/test_ffd_2_0_build2_native_companion_window.py")],cwd=r); raise SystemExit(x.returncode)
