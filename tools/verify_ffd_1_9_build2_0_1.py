#!/usr/bin/env python3
from pathlib import Path
import sys, subprocess
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
checks=[]
def ck(name,value): checks.append((name,bool(value)))
ck('Grounded person narrative service retained',(p/'src/reunion_companion/companion/person_narrative.py').exists())
ck('Mode-separated Biography regression installed',(p/'tests/test_ffd_1_9_build2_person_narrative_presentation.py').exists())
ck('Build 2.0.1 documentation installed',(p/'docs/FFD-1.9-Build-2.0.1.md').exists())
r=subprocess.run([sys.executable,'-m','pytest','-q',str(p/'tests/test_ffd_1_9_build2_person_narrative_presentation.py')],cwd=p)
ck('Research/Presentation Biography separation regression passes',r.returncode==0)
try:
    sys.path.insert(0,str(p/'src'))
    from reunion_companion.companion.version_identity import FFD_DISPLAY, RELEASE_NAME
    ck('Runtime identity updated',FFD_DISPLAY=='FFD 1.9 Build 2.0.1' and RELEASE_NAME=='Research/Presentation Biography Mode Separation')
except Exception:
    ck('Runtime identity updated',False)
for n,v in checks: print(('✓' if v else '✗'),n)
ok=all(v for _,v in checks)
print('\nFFD 1.9 Build 2.0.1 verification '+('PASSED.' if ok else 'FAILED.'))
raise SystemExit(0 if ok else 1)
