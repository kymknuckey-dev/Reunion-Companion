import json,shlex
from .region_dependency_graph import build_from_pipeline,document,write_stage19
from .region_dependency_report import summary,nodes,edges,region,markdown
def handle_build19_command(console,raw_command,command,default_report_path):
    if command.startswith("dependency-report "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: dependency-report "/path/to/pipeline"'
        g,*_=build_from_pipeline(p[1]); target=default_report_path(console.package_path,"region_dependencies"); target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(markdown(g),encoding="utf-8"); js=target.with_suffix(".json"); js.write_text(json.dumps(document(g),indent=2,sort_keys=True),encoding="utf-8"); s19,_=write_stage19(p[1])
        return f"Dependency report written: {target}\nDependency JSON written: {js}\nPipeline Stage 19 artifact written: {s19}"
    if command.startswith("dependency-build "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: dependency-build "/path/to/pipeline"'
        s,g=write_stage19(p[1]); return f"Pipeline Stage 19 artifact: {s}\n{summary(g)}"
    if command.startswith("dependency-region "):
        p=shlex.split(raw_command)
        if len(p)!=3:return 'Usage: dependency-region CR-ID "/path/to/pipeline"'
        g,*_=build_from_pipeline(p[2]); return region(g,p[1])
    if command.startswith("dependency-edges "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: dependency-edges "/path/to/pipeline"'
        g,*_=build_from_pipeline(p[1]); return edges(g)
    if command.startswith("dependency-nodes "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: dependency-nodes "/path/to/pipeline"'
        g,*_=build_from_pipeline(p[1]); return nodes(g)
    if command.startswith("dependency-summary "):
        p=shlex.split(raw_command)
        if len(p)!=2:return 'Usage: dependency-summary "/path/to/pipeline"'
        g,*_=build_from_pipeline(p[1]); return summary(g)
    return None
