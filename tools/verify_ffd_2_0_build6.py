#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
tests=[repo/'tests/test_ffd_2_0_build4_self_contained_runtime.py',repo/'tests/test_ffd_2_0_build5_installation_first_run.py',repo/'tests/test_ffd_2_0_build6_distribution_packaging.py']
r=subprocess.run([sys.executable,'-m','pytest','-q',*[str(x) for x in tests]],cwd=repo)
if r.returncode: raise SystemExit(r.returncode)
r=subprocess.run([sys.executable,str(repo/'macos_app/package_dmg.py'),'--plan'],cwd=repo)
if r.returncode: raise SystemExit(r.returncode)
print('\nFFD 2.0 Build 6 verification PASSED.')
