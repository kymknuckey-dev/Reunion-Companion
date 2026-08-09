from __future__ import annotations
from pathlib import Path
import hashlib
import shutil
import subprocess

IMAGE_EXT={".jpg",".jpeg",".png",".gif",".webp"}

def _asset_dir(output_html):
    output_html=Path(output_html).expanduser()
    d=output_html.parent/(output_html.stem+"_assets")
    d.mkdir(parents=True,exist_ok=True)
    return d

def _safe_name(path,media_id=None):
    import re
    p=Path(path)
    name=re.sub(r"[^A-Za-z0-9._ -]+","_",p.name).strip() or f"media_{media_id or 'item'}"
    return f"{media_id}_{name}" if media_id is not None else name

def copy_original(path,output_html,media_id=None):
    p=Path(path).expanduser()
    if not p.is_file() or output_html is None:
        return None
    assets=_asset_dir(output_html)
    target=assets/_safe_name(p,media_id)
    try:
        if not target.exists() or target.stat().st_size != p.stat().st_size:
            shutil.copy2(p,target)
    except OSError:
        return None
    return f"{assets.name}/{target.name}"

def _cache_prefix(path,media_id=None):
    p=Path(path)
    try:
        stat=p.stat()
        fingerprint=f"{p.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    except OSError:
        fingerprint=str(p)
    h=hashlib.sha1(fingerprint.encode("utf-8","replace")).hexdigest()[:10]
    return f"{media_id or 'doc'}_{h}"

def _render_with_pymupdf(pdf,assets,prefix,dpi=150):
    import pymupdf as fitz
    doc=fitz.open(pdf)
    pages=[]
    scale=dpi/72.0
    matrix=fitz.Matrix(scale,scale)
    for i,page in enumerate(doc):
        rect=page.rect
        orientation="landscape" if rect.width > rect.height else "portrait"
        target=assets/f"{prefix}_page_{i+1:03d}.png"
        if not target.exists():
            pix=page.get_pixmap(matrix=matrix,alpha=False)
            pix.save(target)
        pages.append({
            "page":i+1,
            "orientation":orientation,
            "width_pt":float(rect.width),
            "height_pt":float(rect.height),
            "preview":target,
        })
    doc.close()
    return pages

def _render_first_page_macos(pdf,assets,prefix):
    """Fallback for macOS when PyMuPDF is unavailable.

    sips renders the first PDF page. Multi-page print rendering therefore
    requires PyMuPDF, but the web publication still receives a useful preview.
    """
    target=assets/f"{prefix}_page_001.png"
    try:
        r=subprocess.run(
            ["sips","-s","format","png",str(pdf),"--out",str(target)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60
        )
    except Exception:
        return []
    if r.returncode or not target.exists():
        return []
    # sips does not expose page geometry here. Inspect raster dimensions if Pillow exists.
    orientation="portrait"
    try:
        from PIL import Image
        with Image.open(target) as im:
            orientation="landscape" if im.width > im.height else "portrait"
    except Exception:
        pass
    return [{"page":1,"orientation":orientation,"width_pt":0.0,"height_pt":0.0,"preview":target}]

def render_pdf(path,output_html,media_id=None,dpi=150):
    p=Path(path).expanduser()
    if not p.is_file() or p.suffix.lower()!=".pdf" or output_html is None:
        return {"original":None,"pages":[],"renderer":"none","warning":None}

    original=copy_original(p,output_html,media_id)
    assets=_asset_dir(output_html)
    prefix=_cache_prefix(p,media_id)

    try:
        pages=_render_with_pymupdf(p,assets,prefix,dpi=dpi)
        renderer="PyMuPDF"
        warning=None
    except Exception:
        pages=_render_first_page_macos(p,assets,prefix)
        renderer="macOS sips" if pages else "none"
        warning=(
            None if pages else
            "PDF preview unavailable. Install PyMuPDF for rendered PDF pages."
        )
        if pages:
            warning="Only the first PDF page could be rendered. Install PyMuPDF for all-page print rendering."

    for x in pages:
        x["preview_rel"]=f"{assets.name}/{x['preview'].name}"
    return {"original":original,"pages":pages,"renderer":renderer,"warning":warning}

def pdf_render_capability():
    try:
        import pymupdf as fitz
        return {"available":True,"renderer":"PyMuPDF","all_pages":True}
    except Exception:
        if shutil.which("sips"):
            return {"available":True,"renderer":"macOS sips","all_pages":False}
        return {"available":False,"renderer":"none","all_pages":False}
