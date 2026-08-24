from pathlib import Path
from datetime import datetime
import subprocess
import shutil
from .beta3_data_manager import ensure_companion_tables
from .publishing_v11 import write_family_chapter,write_book,write_book_pdf
from .publishing_v8 import write_biography
from .publishing_v7 import write_person_report,write_family_report
from .publish_profile import write_profile
from .publishing_v10 import descendant_chart_html_document
from .family_publication_model import family_partners
from .descendant_report import write_descendant_report,write_descendant_report_pdf
from .publication_themes import DEFAULT_THEME
from .family_files import active_family_file, ensure_family_files

def _record(db,kind,subject,path,fmt):
    ensure_companion_tables(db); ensure_family_files(db)
    ff=active_family_file(db); wid=ff['id'] if ff else None
    cols={r['name'] for r in db.execute('PRAGMA table_info(companion_publication_history)')}
    if 'workspace_id' in cols:
        db.execute("INSERT INTO companion_publication_history(created_at,kind,subject,output_path,output_format,workspace_id) VALUES(?,?,?,?,?,?)",
                   (datetime.now().isoformat(timespec="seconds"),kind,subject,str(path),fmt,wid))
    else:
        db.execute("INSERT INTO companion_publication_history(created_at,kind,subject,output_path,output_format) VALUES(?,?,?,?,?)",
                   (datetime.now().isoformat(timespec="seconds"),kind,subject,str(path),fmt))
    db.commit();return str(path)

def publication_history(db,limit=10):
    ensure_companion_tables(db); ensure_family_files(db)
    ff=active_family_file(db); cols={r['name'] for r in db.execute('PRAGMA table_info(companion_publication_history)')}
    if ff and 'workspace_id' in cols:
        return [dict(x) for x in db.execute("SELECT * FROM companion_publication_history WHERE workspace_id=? ORDER BY id DESC LIMIT ?",(ff['id'],limit)).fetchall()]
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
    """Existing Publish family action, now backed by the RC1.0.12 standalone report."""
    h,w=family_partners(db,fid)
    start=h or w
    if not start:
        raise ValueError("The selected family has no recorded partner to start the descendant report.")
    p=write_descendant_report(db,start["id"],None,generations,fid,DEFAULT_THEME)
    return _record(db,"Descendant Report",subject,p,"HTML")

def person_output(db,pid,subject,kind):
    funcs={"profile":(write_profile,"Research Profile"),"biography":(write_biography,"Biography"),
           "person":(write_person_report,"Person Report"),"family":(write_family_report,"Family Report"),
           "book":(write_book,"Family-history Book"),"book-pdf":(write_book_pdf,"Family-history Book")}
    f,label=funcs[kind];p=f(db,pid);fmt="PDF" if str(p).lower().endswith(".pdf") else "HTML"
    return _record(db,label,subject,p,fmt)

def scoped_book_output(db,start_pid,end_pid,selected_family_ids,subject,fmt='PDF',generations=4):
    if fmt.upper()=='HTML':
        p=write_book(db,start_pid,None,generations,DEFAULT_THEME,end_pid,selected_family_ids)
        return _record(db,'Family-history Book',subject,p,'HTML')
    p=write_book_pdf(db,start_pid,None,generations,DEFAULT_THEME,end_pid,selected_family_ids)
    return _record(db,'Family-history Book',subject,p,'PDF')

def standalone_descendant_report_output(db,start_pid,subject,generations=3,family_id=None,fmt='HTML'):
    """Generate the RC1.0.12 standalone descendant report without changing Publish UI."""
    if fmt.upper()=='PDF':
        p=write_descendant_report_pdf(db,start_pid,None,generations,family_id,DEFAULT_THEME)
        return _record(db,"Descendant Report",subject,p,"PDF")
    p=write_descendant_report(db,start_pid,None,generations,family_id,DEFAULT_THEME)
    return _record(db,"Descendant Report",subject,p,"HTML")

def open_output(path):
    p=Path(path).expanduser()
    if not p.exists():raise FileNotFoundError(str(p))
    subprocess.Popen(["open",str(p)]);return str(p)


def remove_history(db, history_id):
    ensure_companion_tables(db)
    db.execute("DELETE FROM companion_publication_history WHERE id=?",(history_id,));db.commit()

def delete_publication(db, history_id):
    ensure_companion_tables(db)
    row=db.execute("SELECT output_path FROM companion_publication_history WHERE id=?",(history_id,)).fetchone()
    if not row:return False
    p=Path(row["output_path"]).expanduser()
    if p.exists() and p.is_file():
        p.unlink()
    # Report renderers keep copied media in a dedicated sibling <report>_assets directory.
    # Delete only that exact, report-owned directory; never infer or remove broader folders.
    assets=p.parent/(p.stem+"_assets")
    if assets.exists() and assets.is_dir():
        shutil.rmtree(assets)
    remove_history(db,history_id);return True
