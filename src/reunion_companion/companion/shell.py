from pathlib import Path
import shlex
import subprocess,sys
from .database import connect
from .gedcom import import_gedcom
from .queries import search_people,resolve_person,find_by_event,media_search
from .reporting import person_markdown
from .discovery import rebuild_discovery_index
from .discovery_report import (
    format_tell,format_timeline,format_connections,format_family,format_place,
    format_find,format_gaps,format_research,format_ancestors,format_descendants,
    format_explore
)
from .repair import (
    format_notes,format_note_types,format_sources,format_evidence,format_source,
    format_source_usage,format_citation_summary,summary as repair_summary
)
from .guided import (
    answer_question,format_guided,format_case,format_topic,format_military,
    format_documents
)
from .entities import format_resolve
from .intelligence import (
    records_for_person,format_assess,format_issues,format_unsupported,format_conflicts
)
from .knowledge_graph import format_path,format_neighbourhood,format_evidence_graph,format_topic_graph
from .publishing_v7 import write_person_report,write_family_report
from .relationship_engine import format_relationship
from .story_engine import format_story
from .research_engine import format_improve
from .evidence_engine import format_evidence_intelligence
from .timeline_engine import format_timeline_intelligence
from .knowledge_card import format_card
from .audit_engine import format_audit
from .publishing_v8 import write_biography
from .profile_builder import format_profile
from .confidence_engine import format_confidence
from .gap_engine import format_research_gaps
from .evidence_summary import format_evidence_summary
from .media_health import format_media_health
from .research_timeline import format_research_timeline
from .publish_profile import write_profile
from .publication_themes import format_themes,DEFAULT_THEME,theme_names
from .family_publication_model import resolve_family_for_people,spouse_families,family_partners
from .publishing_v10 import (
    preview_family,descendant_chart_html_document
)
from .publishing_v11 import (
    write_family_chapter,write_book,write_book_pdf,format_publish_capabilities
)

HELP="""Commands:
  ui                                      Open Beta 1 local user interface
  import-gedcom "/path/tree.ged"
  summary
  people TEXT
  person PERSON

Guided Discovery:
  ask "QUESTION"
  resolve "TEXT"
  records PERSON
  guided PERSON
  case PERSON [TOPIC]
  topic TEXT
  military [TEXT]
  documents [TEXT]

Research Intelligence:
  profile [PERSON]             Integrated research profile
  confidence [PERSON]          Evidence/consistency confidence
  research-timeline [PERSON]   Events + dated notes + dated media
  evidence-summary [PERSON]    Compact source/evidence summary
  research-gaps                Database-wide research gap dashboard
  media-health                 Media archive health and legacy audit
  assess PERSON
  issues PERSON
  unsupported PERSON
  conflicts PERSON

Genealogical Intelligence:
  open PERSON                 Open a person workspace
  close                       Leave current workspace
  card [PERSON]               Knowledge Card
  story [PERSON]              Evidence-bound life story
  life-chapters [PERSON]      Human-readable timeline chapters
  relationship PERSON [PERSON] Explain genealogical relationship
  evidence-intelligence [PERSON]
  improve [PERSON]            Research opportunities
  audit [PERSON]              Consistency/evidence audit

Knowledge Graph:
  graph PERSON [DEPTH]
  evidence-graph PERSON
  path "PERSON A" "PERSON B"
  topic-graph TEXT

Professional Publishing & Book:
  publication-capabilities                Show PDF/web/print rendering capabilities
  publication-themes                      Show available publication themes
  publication-theme [NAME]                Show/set active theme
  preview-family PERSON [SPOUSE]           Preview family chapter assembly
  publish-family-chapter PERSON [SPOUSE]   Build professional family chapter
  publish-descendant-chart PERSON [SPOUSE] [GENERATIONS]
  publish-book PERSON [GENERATIONS]        Build HTML book + assets + contents/indexes
  publish-book-pdf PERSON [GENERATIONS]    Build print-ready PDF book

Publishing (earlier foundations):
  publish-profile PERSON [FILE.html]
  publish-biography PERSON [FILE.html]
  publish-person PERSON [FILE.html]
  publish-family PERSON [FILE.html]

Examples:
  ask "What do we know about Lionel George Waight?"
  ask "Why do we think Lionel George Waight was adopted?"
  ask "Who served in Borneo?"
  ask "What records mention Victor Harbor?"
  ask "How is Mervyn Neil Knuckey related to Lionel George Waight?"

Discovery:
  tell PERSON
  timeline PERSON
  family PERSON
  connections PERSON
  ancestors PERSON [GENERATIONS]
  descendants PERSON [GENERATIONS]
  place TEXT
  find TEXT
  research PERSON
  gaps PERSON
  explore PERSON

Referenced notes & citations:
  notes PERSON
  note-types
  sources PERSON
  source ID
  source-usage ID
  citation-summary
  evidence PERSON
  rebuild-index

Existing:
  event TYPE [TEXT]
  media [TEXT]
  media-missing
  report-person PERSON [FILE]
  help
  quit
"""

def _rows(rows,cols):
    if not rows:return "(none)"
    widths={c:len(c) for c in cols};vals=[]
    for r in rows:
        d={c:str(r[c] if r[c] is not None else "") for c in cols}
        for c,v in d.items():widths[c]=min(70,max(widths[c],len(v)))
        vals.append(d)
    return "\n".join(
        ["  ".join(c.ljust(widths[c]) for c in cols),
         "  ".join("-"*widths[c] for c in cols)]
        +["  ".join(d[c][:widths[c]].ljust(widths[c]) for c in cols) for d in vals]
    )

class CompanionShell:
    def __init__(self,db_path):
        self.db_path=Path(db_path).expanduser()
        self.db=connect(self.db_path)
        self.current_person=None
        self.publication_theme=DEFAULT_THEME

    def _resolve(self,t):
        ids=resolve_person(self.db,t)
        if not ids:return None,"Person not found."
        if len(ids)>1:
            rs=[self.db.execute("""SELECT p.id,p.display_name,
                    MAX(CASE WHEN e.event_type='Birth' THEN e.date_text END) birth,
                    MAX(CASE WHEN e.event_type='Death' THEN e.date_text END) death,
                    p.sex,p.gedcom_xref
                    FROM people p LEFT JOIN events e ON e.person_id=p.id
                    WHERE p.id=? GROUP BY p.id""",(i,)).fetchone() for i in ids]
            return None,"Multiple matches:\n"+_rows(rs,("id","display_name","birth","death","sex","gedcom_xref"))
        return ids[0],None

    def _pc(self,p,f):
        if len(p)<2:return f"Usage: {p[0]} PERSON"
        pid,e=self._resolve(" ".join(p[1:]))
        return e or f(self.db,pid)


    def _pc_output(self,p,writer):
        if len(p)<2:return f"Usage: {p[0]} PERSON [FILE.html]"
        output=None;toks=p[1:]
        if toks and (toks[-1].lower().endswith('.html') or '/' in toks[-1]):
            output=toks[-1];toks=toks[:-1]
        pid,e=self._resolve(" ".join(toks))
        if e:return e
        path=writer(self.db,pid,output)
        return f"Report written: {path}"


    def _current_name(self):
        if not self.current_person:return None
        r=self.db.execute("SELECT display_name FROM people WHERE id=?",(self.current_person,)).fetchone()
        return r["display_name"] if r else None

    def _pid_from_optional(self,p):
        if len(p)>1:
            pid,e=self._resolve(" ".join(p[1:]))
            return pid,e
        if self.current_person:
            return self.current_person,None
        return None,f"Usage: {p[0]} PERSON (or open a person first)"

    def _optional_person_command(self,p,func):
        pid,e=self._pid_from_optional(p)
        return e or func(self.db,pid)


    def _family_from_tokens(self,toks):
        """Resolve PERSON [SPOUSE] conservatively."""
        if not toks:
            return None,"Usage requires PERSON [SPOUSE]"
        pid,e=self._resolve(" ".join(toks))
        if pid:
            fams=spouse_families(self.db,pid)
            if len(fams)==1:
                return fams[0],None
            if not fams:
                return None,"No spouse family is recorded for that person."
            names=[]
            for f in fams:
                h,w=family_partners(self.db,f["id"])
                names.append(f"{f['id']}: "+(" and ".join(x["display_name"] for x in (h,w) if x)))
            return None,"Multiple spouse families; specify the spouse name.\n"+"\n".join(names)
        if len(toks)==2:
            a,e1=self._resolve(toks[0]); b,e2=self._resolve(toks[1])
            if a and b:
                f=resolve_family_for_people(self.db,a,b)
                return (f,None) if f else (None,"Those two people are not recorded as partners in one family.")
            return None,e1 or e2 or "Family not found."
        return None,'Could not resolve family. Quote person names, e.g. preview-family "Person One" "Person Two".'

    def command(self,raw):
        try:p=shlex.split(raw)
        except ValueError as e:return f"Command parse error: {e}"
        if not p:return ""
        c=p[0].lower()
        if c=="ui":
            subprocess.Popen([sys.executable,"-m","reunion_companion.companion.ui","--db",str(self.db_path)])
            return "Beta 3.2 Sprint 1 user interface opening at http://127.0.0.1:8765/"
        if c=="help":return HELP
        if c in ("quit","exit"):return None

        if c=="import-gedcom":
            if len(p)!=2:return 'Usage: import-gedcom "/path/tree.ged"'
            r=import_gedcom(self.db,p[1])
            return "Imported GEDCOM\n"+"\n".join(f"  {k:<20} {v}" for k,v in r.items())

        if c=="summary":return repair_summary(self.db)
        if c=="rebuild-index":
            rebuild_discovery_index(self.db);return "Discovery index rebuilt."

        # Foundation 6 entity-first guided layer.
        if c=="ask":
            if len(p)<2:return 'Usage: ask "QUESTION"'
            return answer_question(self.db," ".join(p[1:]))
        if c=="resolve":
            return format_resolve(self.db," ".join(p[1:])) if len(p)>1 else 'Usage: resolve "TEXT"'
        if c=="records":return self._pc(p,records_for_person)
        if c=="assess":return self._pc(p,format_assess)
        if c=="issues":return self._pc(p,format_issues)
        if c=="unsupported":return self._pc(p,format_unsupported)
        if c=="conflicts":return self._pc(p,format_conflicts)
        if c=="guided":return self._pc(p,format_guided)
        if c=="case":
            if len(p)<2:return "Usage: case PERSON [TOPIC]"
            # Resolve the longest prefix that forms a unique person; IDs and xrefs are easy.
            if p[1].isdigit() or p[1].startswith("@I"):
                pid,e=self._resolve(p[1]);term=" ".join(p[2:]) or None
                return e or format_case(self.db,pid,term)
            # Quoted names arrive as one token. Unquoted names can be resolved progressively.
            for end in range(len(p),1,-1):
                pid,e=self._resolve(" ".join(p[1:end]))
                if pid:
                    return format_case(self.db,pid," ".join(p[end:]) or None)
            return "Person not found."
        if c=="topic":
            return format_topic(self.db," ".join(p[1:])) if len(p)>1 else "Usage: topic TEXT"
        if c=="military":
            return format_military(self.db," ".join(p[1:]) if len(p)>1 else None)
        if c=="documents":
            return format_documents(self.db," ".join(p[1:]) if len(p)>1 else None)


        # Foundation 10 Timeline Intelligence Engine.
        if c=="publication-capabilities":
            return format_publish_capabilities()
        if c=="publication-themes":
            return format_themes()
        if c=="publication-theme":
            if len(p)==1:return f"Active publication theme: {self.publication_theme}"
            name=" ".join(p[1:])
            matches=[x for x in theme_names() if x.lower()==name.lower()]
            if not matches:return "Unknown theme. Use publication-themes."
            self.publication_theme=matches[0]
            return f"Publication theme set to: {self.publication_theme}"
        if c=="preview-family":
            fam,e=self._family_from_tokens(p[1:])
            return e or preview_family(self.db,fam["id"])
        if c=="publish-family-chapter":
            fam,e=self._family_from_tokens(p[1:])
            if e:return e
            path=write_family_chapter(self.db,fam["id"],None,self.publication_theme,4)
            return f"Family chapter written: {path}"
        if c=="publish-descendant-chart":
            toks=p[1:];gens=4
            if toks and toks[-1].isdigit():
                gens=max(1,min(8,int(toks[-1])));toks=toks[:-1]
            fam,e=self._family_from_tokens(toks)
            if e:return e
            h,w=family_partners(self.db,fam["id"])
            path=descendant_chart_html_document(self.db,h["id"] if h else None,w["id"] if w else None,None,gens,self.publication_theme)
            return f"Descendant chart written: {path}"
        if c=="publish-book":
            if len(p)<2:return 'Usage: publish-book PERSON [GENERATIONS]'
            toks=p[1:];gens=4
            if toks and toks[-1].isdigit():
                gens=max(1,min(8,int(toks[-1])));toks=toks[:-1]
            pid,e=self._resolve(" ".join(toks))
            if e:return e
            path=write_book(self.db,pid,None,gens,self.publication_theme)
            return f"Family-history book written: {path}"

        if c=="publish-book-pdf":
            if len(p)<2:return 'Usage: publish-book-pdf PERSON [GENERATIONS]'
            toks=p[1:];gens=4
            if toks and toks[-1].isdigit():
                gens=max(1,min(8,int(toks[-1])));toks=toks[:-1]
            pid,e=self._resolve(" ".join(toks))
            if e:return e
            try:
                path=write_book_pdf(self.db,pid,None,gens,self.publication_theme)
            except RuntimeError as err:
                return str(err)
            return f"Print-ready family-history PDF written: {path}"

        # Foundation 9 research intelligence.
        if c=="profile":return self._optional_person_command(p,format_profile)
        if c=="confidence":return self._optional_person_command(p,format_confidence)
        if c=="research-timeline":return self._optional_person_command(p,format_research_timeline)
        if c=="evidence-summary":return self._optional_person_command(p,format_evidence_summary)
        if c=="research-gaps":return format_research_gaps(self.db)
        if c=="media-health":return format_media_health(self.db)
        if c=="publish-profile":
            if len(p)==1 and self.current_person:
                path=write_profile(self.db,self.current_person,None)
                return f"Research profile written: {path}"
            return self._pc_output(p,write_profile)

        # Foundation 8 genealogical intelligence and workspace.
        if c=="open":
            if len(p)<2:return "Usage: open PERSON"
            pid,e=self._resolve(" ".join(p[1:]))
            if e:return e
            self.current_person=pid
            return format_card(self.db,pid)+"\n\nWorkspace opened. Foundation 9 commands such as profile, confidence, research-timeline, evidence-summary, story, improve and audit now use this person by default."
        if c=="close":
            old=self._current_name()
            self.current_person=None
            return f"Workspace closed{': '+old if old else ''}."
        if c=="card":return self._optional_person_command(p,format_card)
        if c=="story":return self._optional_person_command(p,format_story)
        if c=="life-chapters":return self._optional_person_command(p,format_timeline_intelligence)
        if c=="evidence-intelligence":return self._optional_person_command(p,format_evidence_intelligence)
        if c=="improve":return self._optional_person_command(p,format_improve)
        if c=="audit":return self._optional_person_command(p,format_audit)
        if c=="relationship":
            if self.current_person and len(p)>=2:
                b,e=self._resolve(" ".join(p[1:]))
                return e or format_relationship(self.db,self.current_person,b)
            if len(p)==3:
                a,e1=self._resolve(p[1]);b,e2=self._resolve(p[2])
                return e1 or e2 or format_relationship(self.db,a,b)
            return 'Usage: relationship "PERSON A" "PERSON B" or open PERSON then relationship "PERSON B"'
        if c=="publish-biography":
            if len(p)==1 and self.current_person:
                path=write_biography(self.db,self.current_person,None)
                return f"Biography written: {path}"
            return self._pc_output(p,write_biography)

        # Foundation 7 knowledge graph and publishing.
        if c=="graph":
            toks=p[1:];depth=2
            if toks and toks[-1].isdigit() and len(toks)>1:
                depth=max(1,min(8,int(toks[-1])));toks=toks[:-1]
            pid,e=self._resolve(" ".join(toks)) if toks else (None,"Usage: graph PERSON [DEPTH]")
            return e or format_neighbourhood(self.db,pid,depth)
        if c=="evidence-graph":return self._pc(p,format_evidence_graph)
        if c=="topic-graph":return format_topic_graph(self.db," ".join(p[1:])) if len(p)>1 else "Usage: topic-graph TEXT"
        if c=="path":
            if len(p)!=3:return 'Usage: path "PERSON A" "PERSON B"'
            a,e1=self._resolve(p[1]); b,e2=self._resolve(p[2])
            return e1 or e2 or format_path(self.db,a,b)
        if c=="publish-person":return self._pc_output(p,write_person_report)
        if c=="publish-family":return self._pc_output(p,write_family_report)

        if c=="people":
            return _rows(search_people(self.db," ".join(p[1:])),("id","display_name","sex","gedcom_xref")) if len(p)>1 else "Usage: people TEXT"
        if c=="person":
            if len(p)<2:return "Usage: person PERSON"
            pid,e=self._resolve(" ".join(p[1:]));return e or person_markdown(self.db,pid)

        if c=="tell":return self._pc(p,format_tell)
        if c=="timeline":return self._pc(p,format_timeline)
        if c=="family":return self._pc(p,format_family)
        if c=="connections":return self._pc(p,format_connections)
        if c=="research":return self._pc(p,format_research)
        if c=="gaps":return self._pc(p,format_gaps)
        if c=="explore":return self._pc(p,format_explore)
        if c=="notes":return self._pc(p,format_notes)
        if c=="sources":return self._pc(p,format_sources)
        if c=="evidence":return self._pc(p,format_evidence)
        if c=="note-types":return format_note_types(self.db)
        if c=="source":return format_source(self.db,p[1]) if len(p)>1 else "Usage: source ID"
        if c=="source-usage":return format_source_usage(self.db,p[1]) if len(p)>1 else "Usage: source-usage ID"
        if c=="citation-summary":return format_citation_summary(self.db)

        if c in ("ancestors","descendants"):
            toks=p[1:];g=5
            if toks and toks[-1].isdigit() and len(toks)>1:
                g=int(toks[-1]);toks=toks[:-1]
            pid,e=self._resolve(" ".join(toks))
            return e or (format_ancestors if c=="ancestors" else format_descendants)(self.db,pid,g)

        if c=="place":return format_place(self.db," ".join(p[1:])) if len(p)>1 else "Usage: place TEXT"
        if c=="find":return format_find(self.db," ".join(p[1:])) if len(p)>1 else "Usage: find TEXT"
        if c=="event":
            return _rows(find_by_event(self.db,p[1]," ".join(p[2:]) if len(p)>2 else None),
                         ("id","display_name","event_type","date_text","place_text","value_text")) if len(p)>1 else "Usage: event TYPE [TEXT]"
        if c=="media":
            return _rows(media_search(self.db," ".join(p[1:])),
                         ("id","title","file_path","exists_on_disk","attachment_scope","attachment_label"))
        if c=="media-missing":
            return _rows(media_search(self.db,missing_only=True),
                         ("id","title","file_path","attachment_scope","attachment_label"))
        return f"Unknown command: {c}. Type 'help'."

    def run(self):
        print("========================================================")
        print(" Reunion Companion — Version 1 Beta 3.2 Sprint 1")
        print(" Timeline Intelligence Engine")
        print("========================================================")
        print(f"Database: {self.db_path}\n")
        print(HELP)
        while True:
            try:r=input((self._current_name()+" > ") if self.current_person else "companion> ")
            except (EOFError,KeyboardInterrupt):
                print();break
            x=self.command(r)
            if x is None:break
            if x:print(x)

def run(db_path):
    CompanionShell(db_path).run()
