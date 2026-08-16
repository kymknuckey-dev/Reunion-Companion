from __future__ import annotations

import base64
from functools import lru_cache
from importlib.resources import files

BRAND_NAME = "Reunion Companion"
BRAND_TAGLINE = "Your family history. Together."
BRAND_NAVY = "#102B4E"
BRAND_OLIVE = "#60743A"

@lru_cache(maxsize=None)
def brand_data_uri(name: str) -> str:
    data = files(__package__).joinpath("branding_assets", name).read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def header_brand_html() -> str:
    return (
        "<a class='rc-brand' href='/'>"
        f"<img class='rc-header-mark' src='{brand_data_uri('HeaderMark.png')}' alt=''>"
        "<span>Reunion Companion</span></a>"
    )


def home_brand_html() -> str:
    return (
        "<div class='rc-home-brand'>"
        f"<img class='rc-home-icon' src='{brand_data_uri('AppIcon.png')}' alt='Reunion Companion'>"
        "<div class='rc-home-brand-copy'>"
        "<div class='rc-home-name'>Reunion Companion</div>"
        "<div class='rc-home-tagline'>Your family history. Together.</div>"
        "</div></div>"
    )


def publishing_mark_uri() -> str:
    return brand_data_uri("PublishingMark.png")
