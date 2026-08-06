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
    metadata_link_status: str = "unresolved"

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



_DESCRIPTION_BOOK_RE = re.compile(
    rb"([\x20-\x7e]{3,300}?)book",
)
_COMMENT_RE = re.compile(
    rb"([A-Za-z][A-Za-z0-9 ,.'()&+\-]{8,499}[.!?])\x00+",
)


def _decode_description_candidates(data: bytes) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in _DESCRIPTION_BOOK_RE.finditer(data):
        raw = match.group(1)
        # Keep only the trailing readable phrase after binary/control noise.
        phrase_match = re.search(rb"([A-Za-z][A-Za-z0-9 ,.'()&+-]{2,299})$", raw)
        if phrase_match is None:
            continue
        try:
            value = phrase_match.group(1).decode("utf-8").strip()
        except UnicodeDecodeError:
            continue
        if "." in value and value.lower().endswith(
            (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".pdf")
        ):
            continue
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            values.append(value)
    return values


def _decode_comment_candidates(data: bytes) -> list[str]:
    excluded_fragments = (
        "users/",
        "/users/",
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
        ".heic",
        ".pdf",
        "[[pt:",
    )
    values: list[str] = []
    seen: set[str] = set()
    for match in _COMMENT_RE.finditer(data):
        try:
            value = match.group(1).decode("utf-8").strip()
        except UnicodeDecodeError:
            continue
        lowered = value.casefold()
        if any(fragment in lowered for fragment in excluded_fragments):
            continue
        # Comments in the controlled probe are prose; require whitespace and
        # terminal punctuation to avoid picking up internal labels.
        if " " not in value or value[-1:] not in ".!?":
            continue
        key = lowered
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
    descriptions = _decode_description_candidates(data)
    comments = _decode_comment_candidates(data)

    items = sorted(
        grouped.values(),
        key=lambda item: (item.owner_type, item.owner_id, item.media_key),
    )

    # Probe-18 established a one-item mapping. Probe-19 adds a second person
    # image and proves that the filename/path record order matches the stable
    # thumbnail owner order (Person 1, then Person 2). We therefore map by
    # ordered position only when all three cardinalities agree.
    if items and len(items) == len(names) == len(paths):
        for item, filename, original_path in zip(items, names, paths, strict=True):
            item.filename = filename
            item.original_path = original_path
            item.media_type = _media_type(filename)
            item.filename_link_status = "decoded-ordered-controlled-probes"
    elif len(items) == 1:
        item = items[0]
        if names:
            item.filename = names[0]
        if paths:
            item.original_path = paths[0]
            if item.filename is None:
                item.filename = Path(paths[0]).name
        item.media_type = _media_type(item.filename)
        item.filename_link_status = "decoded-single-media-controlled-probe"

    # Probe-20 adds metadata to Mary Probe's image only. A unique metadata
    # pair can therefore be assigned to the sole media item whose owner record
    # contains the description marker. Until a second metadata probe is made,
    # the fallback associates the unique pair with the last ordered media item.
    metadata_targets = [item for item in items if item.owner_type == "person"]
    if descriptions and metadata_targets:
        target = metadata_targets[-1]
        target.description = descriptions[-1]
        if comments:
            target.caption = comments[-1]
        target.metadata_link_status = "decoded-single-metadata-controlled-probe"

    for item in items:
        item.thumbnails.sort(key=lambda thumb: thumb.size_hint)
    return items
