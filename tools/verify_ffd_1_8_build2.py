#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
checks=[('Family File foundation installed',(p/'src/reunion_companion/companion/family_files.py').exists()),('Portable Mac bootstrap installed',(p/'tools/bootstrap_portable_mac.py').exists()),('Build 2 regression installed',(p/'tests/test_ffd_1_8_build2_family_files_portability.py').exists())]
r=subprocess.run([sys.executable,'-m','pytest','-q','tests/test_ffd_1_8_build2_family_files_portability.py'],cwd=p)
checks.append(('Family File regression passes',r.returncode==0))
for n,v in checks:print(('✓' if v else '✗'),n)
ok=all(v for _,v in checks);print('\nFFD 1.8 Build 2 verification '+('PASSED.' if ok else 'FAILED.'));raise SystemExit(0 if ok else 1)
