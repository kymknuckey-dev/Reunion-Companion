#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,importlib.util,tempfile
repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
tests=[repo/"tests/test_ffd_2_0_build4_self_contained_runtime.py",repo/"tests/test_ffd_2_0_build5_installation_first_run.py"]
r=subprocess.run([sys.executable,"-m","pytest","-q",*[str(x) for x in tests]],cwd=repo)
if r.returncode: raise SystemExit(r.returncode)
spec=importlib.util.spec_from_file_location("b5builder",repo/"macos_app/build_app.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
swift=m.swift_source(repo)
assert "Welcome to Reunion Companion" in swift and "/setup/import" in swift
swiftc=m.make_plan(repo).swiftc
if swiftc:
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/"Launcher.swift";f.write_text(swift)
        r=subprocess.run([swiftc,"-typecheck",str(f),"-framework","AppKit","-framework","WebKit","-framework","UniformTypeIdentifiers"])
        if r.returncode: raise SystemExit(r.returncode)
r=subprocess.run([sys.executable,str(repo/"macos_app/build_app.py"),"--plan"],cwd=repo)
if r.returncode: raise SystemExit(r.returncode)
print("\nFFD 2.0 Build 5 verification PASSED.")
