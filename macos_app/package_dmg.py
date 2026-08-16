#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse, plistlib, shutil, subprocess, tempfile

APP_NAME="Reunion Companion"
APP_BUILD="6"
APP_RELEASE="FFD 2.0 RC1.0.5 — Application Identity & Distribution Polish — Visual QA Pass 2"
ENGINE_BASELINE="FFD 1.9 RC1"
VOLUME_NAME="Reunion Companion"
DMG_NAME="Reunion Companion.dmg"

@dataclass(frozen=True)
class PackagePlan:
    repo: Path
    release_dir: Path
    dmg: Path
    hdiutil: str

def repository_root()->Path: return Path(__file__).resolve().parents[1]
def make_plan(repo:Path|None=None,release_dir:Path|None=None)->PackagePlan:
    repo=(repo or repository_root()).resolve()
    release_dir=(release_dir or repo/'dist'/'release').resolve()
    return PackagePlan(repo,release_dir,release_dir/DMG_NAME,shutil.which('hdiutil') or '')

def validate(plan:PackagePlan)->list[str]:
    problems=[]
    if not plan.repo.joinpath('macos_app/build_app.py').exists(): problems.append('Build 5 application builder was not found.')
    if not plan.hdiutil: problems.append('hdiutil was not found; DMG packaging requires macOS.')
    return problems

def run(cmd:list[str],**kwargs):
    return subprocess.run(cmd,check=True,text=True,**kwargs)

def verify_app_identity(app:Path)->None:
    plist=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    if plist.get('CFBundleDisplayName') != APP_NAME: raise SystemExit('Built application identity is not Reunion Companion.')
    if str(plist.get('CFBundleVersion')) != APP_BUILD:
        raise SystemExit(f"Built application is Build {plist.get('CFBundleVersion')}, expected Build {APP_BUILD}.")
    if plist.get('CFBundleIconFile') != 'ReunionCompanion.icns':
        raise SystemExit('Built application does not declare ReunionCompanion.icns as its bundle icon.')
    icon=app/'Contents/Resources/ReunionCompanion.icns'
    if not icon.is_file() or icon.stat().st_size < 1024:
        raise SystemExit(f'Built application icon missing or invalid: {icon}')
    runtime=app/'Contents/Resources/Runtime/ReunionCompanionBackend/ReunionCompanionBackend'
    if not runtime.is_file(): raise SystemExit(f'Bundled runtime missing: {runtime}')

def package(plan:PackagePlan)->Path:
    problems=validate(plan)
    if problems: raise SystemExit('\n'.join(problems))
    plan.release_dir.mkdir(parents=True,exist_ok=True)
    for old in plan.release_dir.glob('*.dmg'): old.unlink()
    with tempfile.TemporaryDirectory(prefix='reunion-companion-dmg-') as td:
        td=Path(td); app=td/f'{APP_NAME}.app'; stage=td/'volume'; stage.mkdir()
        # Build directly into temporary staging so no duplicate discoverable app is left under repo/dist.
        run([str(plan.repo/'.venv/bin/python'),str(plan.repo/'macos_app/build_app.py'),'--output',str(app)],cwd=plan.repo)
        verify_app_identity(app)
        shutil.copytree(app,stage/app.name,symlinks=True)
        (stage/'Applications').symlink_to('/Applications')
        (stage/'README.txt').write_text('Reunion Companion\n\nDrag Reunion Companion.app to the Applications folder.\nThen eject this disk image and launch Reunion Companion from Applications.\n')
        temp_dmg=td/'Reunion Companion-uncompressed.dmg'
        run([plan.hdiutil,'create','-volname',VOLUME_NAME,'-srcfolder',str(stage),'-ov','-format','UDRW',str(temp_dmg)])
        run([plan.hdiutil,'convert',str(temp_dmg),'-format','UDZO','-imagekey','zlib-level=9','-o',str(plan.dmg)])
    verify_dmg(plan)
    return plan.dmg

def verify_dmg(plan:PackagePlan)->None:
    if not plan.dmg.is_file() or plan.dmg.stat().st_size==0: raise SystemExit('DMG was not produced.')
    run([plan.hdiutil,'verify',str(plan.dmg)],stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix='reunion-companion-mount-') as td:
        mount=Path(td)/'mnt'; mount.mkdir()
        run([plan.hdiutil,'attach','-readonly','-nobrowse','-mountpoint',str(mount),str(plan.dmg)],stdout=subprocess.DEVNULL)
        try:
            app=mount/f'{APP_NAME}.app'
            if not app.is_dir(): raise SystemExit('DMG does not contain Reunion Companion.app.')
            if not (mount/'Applications').is_symlink(): raise SystemExit('DMG does not contain the Applications shortcut.')
            if not (mount/'README.txt').is_file(): raise SystemExit('DMG does not contain installation instructions.')
            verify_app_identity(app)
        finally:
            run([plan.hdiutil,'detach',str(mount)],stdout=subprocess.DEVNULL)

def main():
    ap=argparse.ArgumentParser(description=APP_RELEASE)
    ap.add_argument('--release-dir',type=Path)
    ap.add_argument('--verify-only',type=Path)
    ap.add_argument('--plan',action='store_true')
    args=ap.parse_args(); plan=make_plan(release_dir=args.release_dir)
    if args.verify_only:
        plan=PackagePlan(plan.repo,args.verify_only.expanduser().resolve().parent,args.verify_only.expanduser().resolve(),plan.hdiutil)
        verify_dmg(plan); print(f'Verified: {plan.dmg}'); return
    if args.plan:
        print(f'Release: {APP_RELEASE}\nEngine: {ENGINE_BASELINE}\nOutput: {plan.dmg}\nPackaging: hdiutil UDZO\nSigning: not part of Build 6\nNotarisation: not part of Build 6'); return
    dmg=package(plan); print(f'Packaged: {dmg}')

if __name__=='__main__': main()
