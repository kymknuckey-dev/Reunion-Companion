import json,shlex
from .identity_archaeology import build_from_pipeline,identity_document,write_stage22
from .identity_archaeology_report import format_identity_summary,format_identity_keys,format_identity_region,identity_markdown

def handle_build22_command(console,raw_command,command,default_report_path):
    if command.startswith("identity-report "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: identity-report "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);t=default_report_path(console.package_path,"identity_archaeology");t.parent.mkdir(parents=True,exist_ok=True)
        t.write_text(identity_markdown(s),encoding="utf-8");j=t.with_suffix(".json");j.write_text(json.dumps(identity_document(s),indent=2,sort_keys=True),encoding="utf-8");s22,_=write_stage22(p[1])
        return f"Identity archaeology report written: {t}\nIdentity archaeology JSON written: {j}\nPipeline Stage 22 artifact written: {s22}"
    if command.startswith("identity-build "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: identity-build "/path/to/pipeline"'
        t,s=write_stage22(p[1]);return f"Pipeline Stage 22 artifact: {t}\n{format_identity_summary(s)}"
    if command.startswith("identity-region "):
        p=shlex.split(raw_command)
        if len(p)!=3:return 'Usage: identity-region CR-ID "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[2]);return format_identity_region(s,p[1])
    if command.startswith("identity-keys "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: identity-keys "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);return format_identity_keys(s)
    if command.startswith("identity-summary "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: identity-summary "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);return format_identity_summary(s)
    return None
