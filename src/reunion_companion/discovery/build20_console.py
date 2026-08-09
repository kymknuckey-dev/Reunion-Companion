import json,shlex
from .object_reconstruction import build_from_pipeline,reconstruction_document,write_stage20
from .object_reconstruction_report import format_object_summary,format_object_list,format_object_detail,object_markdown
def handle_build20_command(console,raw_command,command,default_report_path):
    if command.startswith("object-reconstruction-report "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: object-reconstruction-report "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);t=default_report_path(console.package_path,"object_reconstruction");t.parent.mkdir(parents=True,exist_ok=True)
        t.write_text(object_markdown(s),encoding="utf-8");j=t.with_suffix(".json");j.write_text(json.dumps(reconstruction_document(s),indent=2,sort_keys=True),encoding="utf-8");s20,_=write_stage20(p[1])
        return f"Object reconstruction report written: {t}\nObject reconstruction JSON written: {j}\nPipeline Stage 20 artifact written: {s20}"
    if command.startswith("object-reconstruction-build "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: object-reconstruction-build "/path/to/pipeline"'
        t,s=write_stage20(p[1]);return f"Pipeline Stage 20 artifact: {t}\n{format_object_summary(s)}"
    if command.startswith("object-reconstruction-detail "):
        p=shlex.split(raw_command)
        if len(p)!=3:return 'Usage: object-reconstruction-detail OBJECT_ID "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[2]);return format_object_detail(s,p[1])
    if command.startswith("object-reconstruction-list "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: object-reconstruction-list "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);return format_object_list(s)
    if command.startswith("object-reconstruction-summary "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: object-reconstruction-summary "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);return format_object_summary(s)
    return None
