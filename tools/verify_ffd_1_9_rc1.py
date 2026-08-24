#!/usr/bin/env python3
import subprocess
r=subprocess.run(["python","-m","pytest","-q"])
print("\nFFD 1.9 RC1 verification "+("PASSED." if r.returncode==0 else "FAILED."))
raise SystemExit(r.returncode)
