from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .evidence import Evidence


@dataclass(slots=True)
class Thumbnail:
    relative_path: str
    size_hint: int
    byte_size: int
    extension: str


@dataclass(slots=True)
class Media:
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
    evidence: Evidence = field(default_factory=Evidence)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# Backwards-compatible public name used in v0.2-v0.5.
MediaItem = Media
