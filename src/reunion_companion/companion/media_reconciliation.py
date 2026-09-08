from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import os
import stat
import unicodedata
import plistlib
import subprocess


FINDER_TAG_XATTR = "com.apple.metadata:_kMDItemUserTags"
FINDER_INFO_XATTR = "com.apple.FinderInfo"
NOT_REFERENCED_FINDER_TAG = "Reunion - Not Referenced"
# Finder on the user's current macOS writes its standard Red tag as "Red\n1"
# and mirrors that colour in the FinderInfo label bits (0x0002).
NOT_REFERENCED_FINDER_COLOUR = 1


def _xattr_read(path: Path, name: str) -> bytes | None:
    """Read a macOS extended attribute via /usr/bin/xattr.

    The frozen Companion runtime does not expose os.getxattr/setxattr on every
    supported macOS build, so use the system tool Finder itself interoperates
    with.
    """
    try:
        cp=subprocess.run(
            ['/usr/bin/xattr','-px',name,str(path)],
            check=False,capture_output=True,text=True,
        )
        if cp.returncode != 0:
            return None
        text=''.join(cp.stdout.split())
        return bytes.fromhex(text) if text else b''
    except (OSError,ValueError):
        return None


def _xattr_write(path: Path, name: str, raw: bytes) -> None:
    cp=subprocess.run(
        ['/usr/bin/xattr','-wx',name,raw.hex(),str(path)],
        check=False,capture_output=True,text=True,
    )
    if cp.returncode != 0:
        raise OSError((cp.stderr or cp.stdout or f'Unable to write {name}').strip())


def _xattr_remove(path: Path, name: str) -> None:
    cp=subprocess.run(
        ['/usr/bin/xattr','-d',name,str(path)],
        check=False,capture_output=True,text=True,
    )
    # xattr returns non-zero when the attribute is already absent; removal is
    # intentionally idempotent.


def _finder_tags(path: Path) -> list[str]:
    """Return Finder user tags exactly as stored in the binary plist."""
    raw=_xattr_read(path,FINDER_TAG_XATTR)
    if raw is None:
        return []
    try:
        value=plistlib.loads(raw)
        return [str(x) for x in value] if isinstance(value,list) else []
    except (ValueError,TypeError,plistlib.InvalidFileException):
        return []


def _write_finder_tags(path: Path, tags: list[str]) -> None:
    if tags:
        _xattr_write(path,FINDER_TAG_XATTR,plistlib.dumps(tags,fmt=plistlib.FMT_BINARY))
    else:
        _xattr_remove(path,FINDER_TAG_XATTR)


def _tag_name(tag: str) -> str:
    return str(tag).split('\n',1)[0]


def _tag_colour(tag: str) -> int | None:
    parts=str(tag).split('\n',1)
    if len(parts) != 2:
        return None
    try:
        value=int(parts[1])
    except (TypeError,ValueError):
        return None
    return value if 0 <= value <= 7 else None


def _finder_label_code(path: Path) -> int:
    raw=_xattr_read(path,FINDER_INFO_XATTR)
    if not raw or len(raw) < 10:
        return 0
    flags=int.from_bytes(raw[8:10],'big')
    return (flags & 0x000E) >> 1


def _set_finder_label_code(path: Path, code: int) -> None:
    """Set only FinderInfo's colour-label bits, preserving every other bit."""
    raw=_xattr_read(path,FINDER_INFO_XATTR)
    info=bytearray(raw if raw is not None else b'')
    if len(info) < 32:
        info.extend(b'\x00'*(32-len(info)))
    flags=int.from_bytes(info[8:10],'big')
    flags=(flags & ~0x000E) | ((int(code) & 0x7) << 1)
    info[8:10]=flags.to_bytes(2,'big')
    _xattr_write(path,FINDER_INFO_XATTR,bytes(info))


def _native_not_referenced_tag() -> str:
    return f'{NOT_REFERENCED_FINDER_TAG}\n{NOT_REFERENCED_FINDER_COLOUR}'


def set_not_referenced_finder_tags(db, *, remove: bool=False) -> dict:
    """Apply/remove Companion's Finder audit tag to the current unreferenced set.

    Finder maintains coloured tags in two places: the named user-tag plist and
    colour-label bits in com.apple.FinderInfo.  Keep those in sync, matching the
    metadata produced by Finder itself on the user's macOS.  Unrelated named tags
    and unrelated FinderInfo bits are preserved.
    """
    data=reconcile_media(db)
    items=data.get('unreferenced') or []
    changed=0; unchanged=0; failed=[]
    for item in items:
        path=Path(item['path'])
        tags=_finder_tags(path)
        had_ours=any(_tag_name(t)==NOT_REFERENCED_FINDER_TAG for t in tags)
        base=[t for t in tags if _tag_name(t)!=NOT_REFERENCED_FINDER_TAG]
        new=base if remove else base+[_native_not_referenced_tag()]
        try:
            if remove:
                if not had_ours:
                    unchanged+=1
                    continue
                _write_finder_tags(path,new)
                # If another coloured Finder tag remains, preserve a matching
                # label colour. Otherwise clear only the label-colour bits.
                remaining=[c for c in (_tag_colour(t) for t in base) if c]
                _set_finder_label_code(path,remaining[-1] if remaining else 0)
            else:
                current_label=_finder_label_code(path)
                if tags==new and current_label==NOT_REFERENCED_FINDER_COLOUR:
                    unchanged+=1
                    continue
                _write_finder_tags(path,new)
                _set_finder_label_code(path,NOT_REFERENCED_FINDER_COLOUR)
            changed+=1
        except OSError as e:
            failed.append({'path':str(path),'error':str(e)})
    return {
        'tag':NOT_REFERENCED_FINDER_TAG,'remove':remove,'eligible':len(items),
        'changed':changed,'unchanged':unchanged,'failed':failed,
    }

IMAGE_EXT={'.jpg','.jpeg','.png','.gif','.webp','.tif','.tiff','.heic','.bmp'}
PDF_EXT={'.pdf'}
SKIP_NAMES={'.DS_Store'}


def _settings_path() -> Path:
    p=Path.home()/'.reunion-companion'
    p.mkdir(parents=True,exist_ok=True)
    return p/'media-reconciliation.json'


def _workspace_key(db) -> str:
    try:
        row=db.execute("SELECT id FROM companion_family_files WHERE is_active=1 ORDER BY id LIMIT 1").fetchone()
        if row:return str(row['id'] if hasattr(row,'keys') else row[0])
    except Exception:
        pass
    return 'default'


def _load_settings() -> dict:
    try:
        data=json.loads(_settings_path().read_text(encoding='utf-8'))
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}


def configured_media_root(db) -> str | None:
    root=(_load_settings().get(_workspace_key(db)) or '').strip()
    return root or None


def set_media_root(db, root: str) -> str:
    p=Path(root).expanduser()
    if not p.exists() or not p.is_dir():
        raise ValueError('Selected media root is not an accessible folder.')
    data=_load_settings(); data[_workspace_key(db)]=str(p)
    _settings_path().write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    return str(p)


def infer_media_root(db) -> str | None:
    rows=db.execute("SELECT file_path FROM media WHERE coalesce(trim(file_path),'')<>''").fetchall()
    votes=defaultdict(int)
    for row in rows:
        p=Path(row['file_path']).expanduser()
        for parent in (p.parent,*p.parents):
            if parent.name.casefold()=='media':
                votes[str(parent)]+=1
                break
    if votes:
        return max(votes.items(),key=lambda x:(x[1],-len(x[0])))[0]
    parents=[str(Path(r['file_path']).expanduser().parent) for r in rows]
    if not parents:return None
    try:return os.path.commonpath(parents)
    except ValueError:return None


def effective_media_root(db) -> str | None:
    return configured_media_root(db) or infer_media_root(db)


def _norm(path: str | Path) -> str:
    """Normalize media paths for macOS-style identity matching.

    Reunion/GEDCOM paths can preserve different filename case (and Unicode
    composition) from the physical file.  Compare the complete path, but do
    so case-insensitively and with canonical Unicode normalization.
    """
    text=os.path.normpath(os.path.expanduser(str(path)))
    return unicodedata.normalize('NFC',text).casefold()


def _is_cloud_placeholder(path: Path) -> bool:
    """Best-effort detection of macOS dataless/iCloud placeholder files."""
    try:
        flags=path.stat().st_flags
    except (AttributeError,OSError):
        return False
    uf_dataless=getattr(stat,'UF_DATALESS',0x40000000)
    return bool(flags & uf_dataless)


def _scan_files(root: Path):
    out=[]
    try:
        iterator=root.rglob('*')
        for p in iterator:
            try:
                if p.name in SKIP_NAMES or p.name.startswith('._') or not p.is_file():continue
                st=p.stat()
                out.append({
                    'path':str(p),'relative_path':str(p.relative_to(root)),
                    'name':p.name,'extension':p.suffix.lower(),'size':st.st_size,
                    'cloud_placeholder':_is_cloud_placeholder(p),
                })
            except (OSError,PermissionError):
                continue
    except (OSError,PermissionError):
        pass
    return out


def _contexts(db, media_id: int):
    result=[]
    try:
        for r in db.execute("""SELECT p.id person_id,p.display_name,'Person' context_type,NULL event_type
          FROM person_media pm JOIN people p ON p.id=pm.person_id WHERE pm.media_id=?""",(media_id,)).fetchall():
            result.append(dict(r))
        for r in db.execute("""SELECT p.id person_id,p.display_name,'Event' context_type,e.event_type
          FROM event_media em JOIN events e ON e.id=em.event_id JOIN people p ON p.id=e.person_id WHERE em.media_id=?""",(media_id,)).fetchall():
            result.append(dict(r))
        for r in db.execute("""SELECT p.id person_id,p.display_name,'Family' context_type,NULL event_type
          FROM family_media fm JOIN family_members mem ON mem.family_id=fm.family_id JOIN people p ON p.id=mem.person_id
          WHERE fm.media_id=? ORDER BY p.display_name""",(media_id,)).fetchall():
            result.append(dict(r))
    except Exception:
        pass
    seen=set(); unique=[]
    for x in result:
        k=(x.get('person_id'),x.get('context_type'),x.get('event_type'))
        if k not in seen:seen.add(k);unique.append(x)
    return unique


def reconcile_media(db, root: str | None=None):
    root_text=root or effective_media_root(db)
    if not root_text:
        return {'root':None,'configured':False,'root_exists':False,'referenced_found':[], 'referenced_missing':[], 'unreferenced':[], 'cloud_placeholders':[], 'counts':{}}
    root_path=Path(root_text).expanduser()
    physical=_scan_files(root_path) if root_path.exists() else []
    by_norm={_norm(x['path']):x for x in physical}
    refs=db.execute("SELECT id,title,file_path,media_type,exists_on_disk,attachment_scope,attachment_label,is_preferred FROM media ORDER BY id").fetchall()
    referenced_norm=set(); found=[]; missing=[]
    for r in refs:
        x=dict(r); n=_norm(x['file_path']); referenced_norm.add(n)
        disk=by_norm.get(n)
        if disk is None and Path(x['file_path']).expanduser().exists():
            p=Path(x['file_path']).expanduser()
            try:
                disk={'path':str(p),'relative_path':str(p.relative_to(root_path)) if p.is_relative_to(root_path) else str(p), 'name':p.name,'extension':p.suffix.lower(),'size':p.stat().st_size,'cloud_placeholder':_is_cloud_placeholder(p)}
            except Exception:disk=None
        x['contexts']=_contexts(db,int(x['id']))
        if disk:
            x.update(disk); found.append(x)
        else:
            x['name']=Path(x['file_path']).name; x['relative_path']=None; x['cloud_placeholder']=False; missing.append(x)
    unref=[x for x in physical if _norm(x['path']) not in referenced_norm]
    cloud=[]
    found_by_norm={_norm(x.get('path') or x.get('file_path')):x for x in found}
    for disk in physical:
        if not disk.get('cloud_placeholder'):
            continue
        item=dict(disk)
        ref=found_by_norm.get(_norm(disk['path']))
        item['referenced']=bool(ref)
        if ref:
            item['title']=ref.get('title')
            item['media_type']=ref.get('media_type')
            item['contexts']=ref.get('contexts') or []
        cloud.append(item)
    return {
        'root':str(root_path),'configured':bool(configured_media_root(db)),'root_exists':root_path.exists(),
        'referenced_found':found,'referenced_missing':missing,'unreferenced':unref,'cloud_placeholders':cloud,
        'counts':{'referenced':len(refs),'referenced_found':len(found),'referenced_missing':len(missing),'physical':len(physical),'unreferenced':len(unref),'cloud_placeholders':len(cloud)}
    }


def media_file_allowed(db, candidate: str) -> Path | None:
    root=effective_media_root(db)
    if not root:return None
    try:
        rp=Path(root).expanduser().resolve(); cp=Path(candidate).expanduser().resolve()
        cp.relative_to(rp)
    except Exception:return None
    return cp if cp.exists() and cp.is_file() else None
