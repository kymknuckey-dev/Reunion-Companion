import json,shlex
from .person_navigation_archaeology import analyse_manifest,navigation_document,write_stage23,manifest_template
from .person_navigation_report import format_navigation_summary,format_index_candidates,format_change_candidates,format_delta,navigation_markdown

def handle_build23_command(console,raw_command,command,default_report_path):
    if command=="navigation-template":
        return json.dumps(manifest_template(),indent=2)

    if command.startswith("navigation-report "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: navigation-report "/path/navigation_probe.json"'
        s=analyse_manifest(p[1]);t=default_report_path(console.package_path,"person_navigation_archaeology");t.parent.mkdir(parents=True,exist_ok=True)
        t.write_text(navigation_markdown(s),encoding="utf-8");j=t.with_suffix(".json");j.write_text(json.dumps(navigation_document(s),indent=2,sort_keys=True),encoding="utf-8")
        return f"Navigation archaeology report written: {t}\nNavigation archaeology JSON written: {j}"

    if command.startswith("navigation-build "):
        p=shlex.split(raw_command)
        if len(p)!=3:return 'Usage: navigation-build "/path/navigation_probe.json" "/path/to/pipeline"'
        t,s=write_stage23(p[1],p[2]);return f"Pipeline Stage 23 artifact: {t}\n{format_navigation_summary(s)}"

    if command.startswith("navigation-delta "):
        p=shlex.split(raw_command)
        if len(p)!=3:return 'Usage: navigation-delta LABEL "/path/navigation_probe.json"'
        s=analyse_manifest(p[2]);return format_delta(s,p[1])

    if command.startswith("change-log-candidates "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: change-log-candidates "/path/navigation_probe.json"'
        return format_change_candidates(analyse_manifest(p[1]))

    if command.startswith("person-index-candidates "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: person-index-candidates "/path/navigation_probe.json"'
        return format_index_candidates(analyse_manifest(p[1]))

    if command.startswith("navigation-summary "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: navigation-summary "/path/navigation_probe.json"'
        return format_navigation_summary(analyse_manifest(p[1]))

    return None
