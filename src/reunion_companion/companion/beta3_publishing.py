from pathlib import Path
from datetime import datetime
import subprocess
from .beta3_data_manager import ensure_companion_tables
from .publishing_v11 import write_family_chapter,write_book,write_book_pdf
from .publishing_v8 import write_biography
from .publishing_v7 import write_person_report,write_family_report
from .publish_profile import write_profile
from .publishing_v10 import descendant_chart_html_document
from .family_publication_model import family_partners
from .publication_themes import DEFAULT_THEME

def _record(db,kind,subject,path,fmt):
    ensure_companion_tables(db)
    db.execute("INSERT INTO companion_publication_history(created_at,kind,subject,output_path,output_format) VALUES(?,?,?,?,?)",
               (datetime.now().isoformat(timespec="seconds"),kind,subject,str(path),fmt));db.commit();return str(path)

def publication_history(db,limit=30):
    ensure_companion_tables(db)
    return [dict(x) for x in db.execute("SELECT * FROM companion_publication_history ORDER BY id DESC LIMIT ?",(limit,)).fetchall()]

def family_chapter_html(db,fid,subject):
    return _record(db,"Professional Family Chapter",subject,write_family_chapter(db,fid),"HTML")

def family_chapter_pdf(db,fid,subject):
    hp=Path(write_family_chapter(db,fid))
    from weasyprint import HTML
    pp=hp.with_suffix(".pdf");HTML(filename=str(hp)).write_pdf(str(pp))
    _record(db,"Professional Family Chapter",subject,hp,"HTML")
    return _record(db,"Professional Family Chapter",subject,pp,"PDF")

def descendant_chart(db,fid,subject,generations=4):
    h,w=family_partners(db,fid)
    p=descendant_chart_html_document(db,h["id"] if h else None,w["id"] if w else None,None,generations,DEFAULT_THEME)
    return _record(db,"Descendant Chart",subject,p,"HTML")

def person_output(db,pid,subject,kind):
    funcs={"profile":(write_profile,"Research Profile"),"biography":(write_biography,"Biography"),
           "person":(write_person_report,"Person Report"),"family":(write_family_report,"Family Report"),
           "book":(write_book,"Family-history Book"),"book-pdf":(write_book_pdf,"Family-history Book")}
    f,label=funcs[kind];p=f(db,pid);fmt="PDF" if str(p).lower().endswith(".pdf") else "HTML"
    return _record(db,label,subject,p,fmt)

def open_output(path):
    p=Path(path).expanduser()
    if not p.exists():raise FileNotFoundError(str(p))
    subprocess.Popen(["open",str(p)]);return str(p)
