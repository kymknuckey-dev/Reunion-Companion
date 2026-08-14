#!/usr/bin/env python3
from pathlib import Path
import sys, subprocess
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
checks=[]
def ck(n,v): checks.append((n,bool(v)))
ck('Grounded person narrative service installed',(p/'src/reunion_companion/companion/person_narrative.py').exists())
ck('Build 2 regression installed',(p/'tests/test_ffd_1_9_build2_person_narrative_presentation.py').exists())
ck('Build 2 documentation installed',(p/'docs/FFD-1.9-Build-2.md').exists())
r=subprocess.run([sys.executable,'-m','pytest','-q',str(p/'tests/test_ffd_1_9_build2_person_narrative_presentation.py')],cwd=p)
ck('Build 2 narrative/cache/layout regression passes',r.returncode==0)
for n,v in checks: print(('✓' if v else '✗'),n)
ok=all(v for _,v in checks);print('\nFFD 1.9 Build 2 verification '+('PASSED.' if ok else 'FAILED.'));raise SystemExit(0 if ok else 1)
