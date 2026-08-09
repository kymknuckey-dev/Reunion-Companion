import json,shlex
from .object_instance_reconstruction import build_from_pipeline,instance_document,write_stage21
from .object_instance_report import format_instance_summary,format_instance_list,format_instance_detail,instance_markdown

def handle_build21_command(console,raw_command,command,default_report_path):
    if command.startswith("instance-report "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: instance-report "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);t=default_report_path(console.package_path,"object_instances");t.parent.mkdir(parents=True,exist_ok=True)
        t.write_text(instance_markdown(s),encoding="utf-8");j=t.with_suffix(".json");j.write_text(json.dumps(instance_document(s),indent=2,sort_keys=True),encoding="utf-8");s21,_=write_stage21(p[1])
        return f"Object instance report written: {t}\nObject instance JSON written: {j}\nPipeline Stage 21 artifact written: {s21}"
    if command.startswith("instance-build "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: instance-build "/path/to/pipeline"'
        t,s=write_stage21(p[1]);return f"Pipeline Stage 21 artifact: {t}\n{format_instance_summary(s)}"
    if command.startswith("instance-detail "):
        p=shlex.split(raw_command)
        if len(p)!=3:return 'Usage: instance-detail INSTANCE_ID "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[2]);return format_instance_detail(s,p[1])
    if command.startswith("instance-list "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: instance-list "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);return format_instance_list(s)
    if command.startswith("instance-summary "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: instance-summary "/path/to/pipeline"'
        s,*_=build_from_pipeline(p[1]);return format_instance_summary(s)
    return None
