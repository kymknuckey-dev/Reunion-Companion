from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re

from .parser import BinaryReader

_THUMBNAIL_RE = re.compile(
    r"^(?P<owner_type>[pf])(?P<owner_id>\d+)-"
    r"(?P<fingerprint>[0-9a-fA-F]+)-(?P<size>\d+)\.(?P<extension>[A-Za-z0-9]+)$"
)
_MEDIA_NAME_RE = re.compile(
    rb"([A-Za-z0-9 _().,'&+-]{1,200}\.(?:jpe?g|png|tiff?|heic|pdf))",
    re.IGNORECASE,
)
_LOWER_PATH_RE = re.compile(
    rb"(/users/[^\x00\r\n]{1,1000}\.(?:jpe?g|png|tiff?|heic|pdf))",
    re.IGNORECASE,
)


@dataclass(slots=True)
class Thumbnail:
    relative_path: str
    size_hint: int
    byte_size: int
    extension: str


@dataclass(slots=True)
class MediaItem:
    media_key: str
    owner_type: str
    owner_id: int
    fingerprint: str
    filename: str | None = None
    original_path: str | None = None
    media_type: str | None = None
    caption: str | None = None
    description: str | None = None
    thumbnails: list[Thumbnail] = field(default_factory=list)
    filename_link_status: str = "unresolved"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _decode_media_names(data: bytes) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in _MEDIA_NAME_RE.finditer(data):
        try:
            value = match.group(1).decode("utf-8")
        except UnicodeDecodeError:
            continue
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            values.append(value)
    return values


def _decode_original_paths(data: bytes) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in _LOWER_PATH_RE.finditer(data):
        try:
            value = match.group(1).decode("utf-8")
        except UnicodeDecodeError:
            continue
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            values.append(value)
    return values


def _media_type(filename: str | None) -> str | None:
    if not filename or "." not in filename:
        return None
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension in {"jpg", "jpeg", "png", "tif", "tiff", "heic"}:
        return "image"
    if extension == "pdf":
        return "document"
    return extension


def extract_media(package_path: str | Path) -> list[MediaItem]:
    reader = BinaryReader(package_path)
    package = reader.inspect()
    data = reader.read_main_data()

    grouped: dict[tuple[str, int, str], MediaItem] = {}
    thumbnails_root = package.package_path / "thumbnails"
    if thumbnails_root.is_dir():
        for path in sorted(thumbnails_root.rglob("*")):
            if not path.is_file():
                continue
            match = _THUMBNAIL_RE.match(path.name)
            if match is None:
                continue
            owner_code = match.group("owner_type")
            owner_type = "person" if owner_code == "p" else "family"
            owner_id = int(match.group("owner_id"))
            fingerprint = match.group("fingerprint").lower()
            key = (owner_type, owner_id, fingerprint)
            item = grouped.setdefault(
                key,
                MediaItem(
                    media_key=f"{owner_code}{owner_id}-{fingerprint}",
                    owner_type=owner_type,
                    owner_id=owner_id,
                    fingerprint=fingerprint,
                ),
            )
            item.thumbnails.append(
                Thumbnail(
                    relative_path=str(path.relative_to(package.package_path)),
                    size_hint=int(match.group("size")),
                    byte_size=path.stat().st_size,
                    extension=match.group("extension").lower(),
                )
            )

    names = _decode_media_names(data)
    paths = _decode_original_paths(data)

    # Controlled Probe-18 has one logical media item. For a single item, the
    # unique filename/path association is unambiguous. Multi-item ownership
    # remains deliberately unresolved until a second controlled media probe.
    items = sorted(grouped.values(), key=lambda item: (item.owner_type, item.owner_id, item.media_key))
    if len(items) == 1:
        item = items[0]
        if names:
            # Prefer a mixed-case filename over a lower-case sandbox path tail.
            item.filename = names[0]
        if paths:
            item.original_path = paths[0]
            if item.filename is None:
                item.filename = Path(paths[0]).name
        item.media_type = _media_type(item.filename)
        item.filename_link_status = "decoded-single-media-controlled-probe"

    for item in items:
        item.thumbnails.sort(key=lambda thumb: thumb.size_hint)
    return items
