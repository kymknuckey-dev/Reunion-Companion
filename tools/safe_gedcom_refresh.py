#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from reunion_companion.companion.safe_refresh import safe_refresh, safe_reload_current, format_change_summary

ap=argparse.ArgumentParser(description='Safely rebuild Reunion Companion imported data from a Reunion GEDCOM export.')
ap.add_argument('db',help='Companion SQLite database path')
ap.add_argument('gedcom',nargs='?',help='GEDCOM path; omit with --current')
ap.add_argument('--current',action='store_true',help='Refresh the GEDCOM currently recorded by Companion')
ap.add_argument('--dry-run',action='store_true',help='Build/validate/compare but do not replace the working database')
ap.add_argument('--json',action='store_true',help='Print full JSON report')
a=ap.parse_args()
if a.current:
    r=safe_reload_current(a.db,dry_run=a.dry_run)
elif a.gedcom:
    r=safe_refresh(a.db,a.gedcom,dry_run=a.dry_run)
else:
    ap.error('provide GEDCOM path or --current')
if a.json:
    print(json.dumps(r,indent=2,sort_keys=True))
else:
    print('Safe GEDCOM refresh '+('DRY RUN' if a.dry_run else 'COMPLETE'))
    print('Source:',r['source']['path'])
    print('Changes:',format_change_summary(r['changes']))
    print('Validation:',r['validation'])
    if r.get('backup_path'): print('Backup:',r['backup_path'])
