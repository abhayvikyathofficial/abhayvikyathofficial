# writes sections/badges.md
# linkedin + globe icons come from bootstrap icons since shields doesn't have them

import base64
import urllib.request
from pathlib import Path
from urllib.parse import quote

BG = "0A101F"
LOGO = "22D3EE"

GLYPHS = {
    "linkedin": "https://raw.githubusercontent.com/twbs/icons/main/icons/linkedin.svg",
    "globe": "https://raw.githubusercontent.com/twbs/icons/main/icons/globe2.svg",
}

BADGES = [
    ("Portfolio", "https://abhayvikyath.in", ("data", "globe")),
    ("FlipStudio", "https://flipstudio.in", None),
    ("LinkedIn", "https://www.linkedin.com/in/abhayvikyath/", ("data", "linkedin")),
    ("Instagram", "https://www.instagram.com/flipstudioofficial/", ("slug", "instagram")),
    ("X", "https://x.com/abhay_vikyath", ("slug", "x")),
    ("YouTube", "https://www.youtube.com/@flipstudio", ("slug", "youtube")),
    ("Email", "mailto:workswithabhay@gmail.com", ("slug", "gmail")),
]


def data_uri(name):
    svg = urllib.request.urlopen(GLYPHS[name], timeout=30).read().decode()
    svg = svg.replace('fill="currentColor"', f'fill="#{LOGO}"')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def badge_url(label, logo):
    url = f"https://img.shields.io/badge/{quote(label)}-{BG}?style=for-the-badge&labelColor={BG}"
    if logo:
        kind, value = logo
        url += "&logo=" + (quote(data_uri(value), safe="") if kind == "data" else value) + f"&logoColor={LOGO}"
    return url


def main():
    parts = []
    for label, link, logo in BADGES:
        url = badge_url(label, logo)
        parts.append(f'<a href="{link}"><img alt="{label}" src="{url.replace("&", "&amp;")}"></a>')
    block = "<!-- badges -->\n<p align=\"center\">\n  " + "&nbsp;&nbsp;\n  ".join(parts) + "\n</p>\n"
    (Path(__file__).parent / "badges.md").write_text(block, encoding="utf8")


if __name__ == "__main__":
    main()
