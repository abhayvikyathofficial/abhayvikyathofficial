# python sections/build_readme.py

import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
U = "abhayvikyathofficial"
BG = "0A101F"

banner = """<picture>
  <source media="(prefers-color-scheme: dark)" srcset="banner/dark.svg">
  <img alt="Abhay Vikyath - Content &amp; Creative Strategist" width="100%" src="banner/light.svg">
</picture>

<h3 align="center">Content &amp; Creative Strategist</h3>
<p align="center">Design · Content · Marketing · Multimedia · Branding · Digital · AI &amp; Creative Technology</p>
"""


def contribution_count():
    url = f"https://github.com/users/{U}/contributions"
    html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode()
    m = re.search(r"([\d,]+)\s+contributions?\s+in the last year", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)))
    return m.group(1) if m else "?"


# the workflow keeps this number updated
snake_title = f"{contribution_count()} contributions in the last year · hover the graph below for daily counts"

snake = f"""<!-- snake -->
<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{U}/{U}/output/github-snake-dark.svg">
  <img alt="Contribution snake" title="{snake_title}" width="100%" src="https://raw.githubusercontent.com/{U}/{U}/output/github-snake.svg">
</picture>
</p>
"""

# no adobe icons on shields anymore
TOOLS = [
    ("Figma", "figma"),
    ("Adobe Photoshop", None),
    ("Adobe Premiere Pro", None),
    ("After Effects", None),
    ("HTML5", "html5"),
    ("CSS3", "css"),
    ("JavaScript", "javascript"),
]


def tool_badge(label, slug):
    url = f"https://img.shields.io/badge/{label.replace(' ', '_')}-{BG}?style=flat-square"
    if slug:
        url += f"&logo={slug}&logoColor=22D3EE"
    return f'<img alt="{label}" src="{url.replace("&", "&amp;")}">'


toolkit = "<!-- tools -->\n<p align=\"center\">\n  " + "\n  ".join(tool_badge(*t) for t in TOOLS) + "\n</p>\n"

footer = f"""<p align="center">
  <img alt="Profile views" src="https://komarev.com/ghpvc/?username={U}&amp;label=Profile+Views&amp;color={BG}&amp;style=flat">
</p>
"""

stats = (HERE / "stats.md").read_text(encoding="utf8")
badges = (HERE / "badges.md").read_text(encoding="utf8")

readme = "\n".join([banner, stats, snake, badges, toolkit, footer])
(ROOT / "README.md").write_text(readme, encoding="utf8")
