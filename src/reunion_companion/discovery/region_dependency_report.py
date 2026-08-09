def summary(g):
    s={
      "nodes":len(g.nodes),"edges":len(g.edges),"components":len({n.semantic_label for n in g.nodes if not n.semantic_label.startswith("CONTRADICTORY:")}),
      "cross":sum(e.relation=="CROSS_SEMANTIC_SIGNATURE" for e in g.edges),
      "struct":sum(e.relation=="SHARED_STRUCTURAL_SUPPORT" for e in g.edges),
      "arch":sum(e.relation=="ARCHITECTURAL_LINK" for e in g.edges)}
    return "\n".join(["Region Dependency Graph Engine","==============================",
      f"Unique region nodes          {s['nodes']:,}",f"Dependency edges            {s['edges']:,}",
      f"Semantic components         {s['components']:,}",f"Cross-semantic edges        {s['cross']:,}",
      f"Structural-support edges    {s['struct']:,}",f"Architecture edges          {s['arch']:,}",
      f"Duplicate rows collapsed    {g.duplicate_rows_collapsed:,}",f"Contradictory nodes         {g.contradictory_nodes:,}","",
      "Edges are structural hypotheses, not CANONICAL relationships."])

def nodes(g,limit=80):
    lines=["Dependency Graph Nodes","======================","Score   Grade                 Region        Probe                Label"]
    for n in g.nodes[:limit]: lines.append(f"{n.score:>6.1%}  {n.grade:<20} {n.region_id:<13} {n.probe_id:<20} {n.semantic_label}")
    return "\n".join(lines)

def edges(g,limit=100):
    lines=["Dependency Graph Edges","======================","Conf    Relation                    Source        Target"]
    for e in g.edges[:limit]: lines.append(f"{e.confidence:>6.1%}  {e.relation:<27} {e.source:<13} {e.target}")
    return "\n".join(lines)

def region(g,rid):
    n=next((x for x in g.nodes if x.region_id==rid),None)
    if not n:return f"Region not found: {rid}"
    es=[e for e in g.edges if e.source==rid or e.target==rid]
    lines=[f"Dependency Evidence — {rid}","="*(22+len(rid)),f"Label       {n.semantic_label}",f"Probe       {n.probe_id}",f"Confidence  {n.score:.1%}",f"Edges       {len(es)}",""]
    for e in es: lines.append(f"{e.confidence:.1%} {e.relation} -> {e.target if e.source==rid else e.source}")
    return "\n".join(lines)

def markdown(g):
    lines=["# Region Dependency Graph — Build 19","","```text",summary(g),"```","","## Nodes","","| Region | Label | Probe | Score | Grade |","|---|---|---|---:|---|"]
    for n in g.nodes: lines.append(f"| {n.region_id} | {n.semantic_label} | {n.probe_id} | {n.score:.1%} | {n.grade} |")
    lines+=["","## Edges","","| Edge | Relation | Source | Target | Confidence |","|---|---|---|---|---:|"]
    for e in g.edges: lines.append(f"| {e.edge_id} | {e.relation} | {e.source} | {e.target} | {e.confidence:.1%} |")
    lines+=["","## Evidence boundary","","Build 19 models dependency hypotheses only. It does not prove ownership, containment, pointer direction or write semantics."]
    return "\n".join(lines)+"\n"
