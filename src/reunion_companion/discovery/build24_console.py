import json,shlex
from .probe_manifest_engine import discover_probe_snapshots,write_manifest,validate_manifest,run_regression,regression_document
from .probe_manifest_report import format_manifest_result,format_validation,format_regression

def handle_build24_command(console,raw_command,command,default_report_path):
    if command.startswith("probe-manifest-write "):
        p=shlex.split(raw_command)
        if len(p) not in (2,3):return 'Usage: probe-manifest-write "/path/probe-folder" ["/path/navigation_probe.json"]'
        target,result=write_manifest(p[1], p[2] if len(p)==3 else None)
        return f"Manifest written: {target}\n{format_manifest_result(result)}"

    if command.startswith("probe-manifest "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: probe-manifest "/path/probe-folder"'
        return format_manifest_result(discover_probe_snapshots(p[1]))

    if command.startswith("probe-validate "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: probe-validate "/path/navigation_probe.json"'
        return format_validation(validate_manifest(p[1]))

    if command.startswith("probe-regression-report "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: probe-regression-report "/path/navigation_probe.json"'
        r=run_regression(p[1])
        t=default_report_path(console.package_path,"probe_regression");t.parent.mkdir(parents=True,exist_ok=True)
        t.write_text(format_regression(r)+"\n",encoding="utf-8")
        j=t.with_suffix(".json");j.write_text(json.dumps(regression_document(r),indent=2,sort_keys=True),encoding="utf-8")
        return f"Probe regression report written: {t}\nProbe regression JSON written: {j}\n{format_regression(r)}"

    if command.startswith("probe-regression "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: probe-regression "/path/navigation_probe.json"'
        return format_regression(run_regression(p[1]))

    return None
