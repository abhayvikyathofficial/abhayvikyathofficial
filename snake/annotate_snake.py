# adds labels above the snake graph showing what was done on each day it eats
# usage: python snake/annotate_snake.py dist/github-snake.svg light dist/github-snake-dark.svg dark

import json
import os
import re
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "abhayvikyathofficial")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

THEMES = {
    "light": dict(pill="#FFFFFF", stroke="#C4B5FD", text="#0F172A", num="#7C3AED"),
    "dark": dict(pill="#0A101F", stroke="#5B44A8", text="#E2E8F0", num="#22D3EE"),
}

HOLD_MS = 1600
GROUP_MS = 700  # squares eaten this close together get one label
FADE_MS = 60
CHAR_W = 6.1
LABEL_Y = -14


def http_get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0", **(headers or {})})
    return urllib.request.urlopen(req, timeout=30).read().decode()


def calendar():
    html = http_get(f"https://github.com/users/{USER}/contributions")
    tips = {
        m.group(1): m.group(2)
        for m in re.finditer(r'<tool-tip[^>]*for="contribution-day-component-(\d+-\d+)"[^>]*>([^<]*)</tool-tip>', html)
    }
    out = {}
    for date, row, col, level in re.findall(
        r'data-date="([\d-]+)" id="contribution-day-component-(\d+)-(\d+)" data-level="(\d)"', html
    ):
        if level == "0":
            continue
        m = re.match(r"([\d,]+) contribution", tips.get(f"{row}-{col}", ""))
        if m:
            out[f"{row}-{col}"] = (date, int(m.group(1).replace(",", "")))
    return out


def public_commits():
    if not TOKEN:
        return {}
    query = """query($login:String!){user(login:$login){contributionsCollection{
      commitContributionsByRepository(maxRepositories:100){
        repository{name isPrivate}
        contributions(first:100){nodes{occurredAt commitCount}}}}}}"""
    body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
    data = json.loads(
        http_get("https://api.github.com/graphql", body, {"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    )
    out = {}
    for entry in data["data"]["user"]["contributionsCollection"]["commitContributionsByRepository"]:
        if entry["repository"]["isPrivate"]:
            continue
        for node in entry["contributions"]["nodes"]:
            out.setdefault(node["occurredAt"][:10], []).append((entry["repository"]["name"], node["commitCount"]))
    return out


def label_parts(total, repos):
    parts, used = [], 0
    for repo, n in sorted(repos.items(), key=lambda r: -r[1]):
        n = min(n, total - used)
        if n <= 0:
            continue
        parts.append((str(n), f" {'commit' if n == 1 else 'commits'} · {repo}"))
        used += n
    rest = total - used
    if rest > 0:
        parts.append((str(rest), f" {'contribution' if rest == 1 else 'contributions'} · private repo"))
    return parts


def annotate(path, theme, cal, public):
    th = THEMES[theme]
    svg = open(path, encoding="utf-8").read()
    if 'class="snk-label' in svg:
        return 0
    duration = int(re.search(r"animation:none (\d+)ms", svg).group(1))
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    eat = {m.group(1): float(m.group(2)) for m in re.finditer(r"@keyframes (c[0-9a-z]+)\{([\d.]+)%", svg)}

    events = []
    for cls, x, y in re.findall(r'<rect class="c (c[0-9a-z]+)" x="(\d+)" y="(\d+)"', svg):
        col, row = (int(x) - 2) // 16, (int(y) - 2) // 16
        day = cal.get(f"{row}-{col}")
        if day and cls in eat:
            date, total = day
            repos = {}
            for repo, n in public.get(date, []):
                repos[repo] = repos.get(repo, 0) + min(n, total)
            events.append((eat[cls], int(x) + 6, total, repos))
    events.sort()

    to_pct = 100.0 / duration
    groups_ev = []
    for ev in events:
        if groups_ev and ev[0] - groups_ev[-1][0][0] < GROUP_MS * to_pct:
            groups_ev[-1].append(ev)
        else:
            groups_ev.append([ev])

    css, groups = [], []
    for i, grp in enumerate(groups_ev):
        total = sum(e[2] for e in grp)
        repos = {}
        for e in grp:
            for repo, n in e[3].items():
                repos[repo] = repos.get(repo, 0) + n
        parts = label_parts(total, repos)
        xs = [e[1] for e in grp]
        cx = sum(xs) / len(xs)
        text_len = sum(len(a) + len(b) for a, b in parts) + 3 * (len(parts) - 1)
        w = text_len * CHAR_W + 16
        left = min(max(cx - w / 2, vb[0] + 2), vb[0] + vb[2] - w - 2)
        show = grp[0][0]
        nxt = groups_ev[i + 1][0][0] if i + 1 < len(groups_ev) else 100.0
        hide = min(nxt, show + HOLD_MS * to_pct, 99.9)
        fade = FADE_MS * to_pct
        a, b, c, d = show, min(show + fade, hide), max(hide - fade, show + fade), hide
        css.append(
            f"@keyframes l{i}{{0%,{a:.3f}%{{opacity:0}}{b:.3f}%,{c:.3f}%{{opacity:1}}{d:.3f}%,100%{{opacity:0}}}}"
            f".snk-label.l{i}{{animation-name:l{i}}}"
        )
        tspans, first = [], True
        for num, rest in parts:
            if not first:
                tspans.append(f'<tspan fill="{th["text"]}" opacity="0.5"> + </tspan>')
            tspans.append(f'<tspan fill="{th["num"]}" font-weight="700">{escape(num)}</tspan><tspan fill="{th["text"]}">{escape(rest)}</tspan>')
            first = False
        pointers = "".join(
            f'<line x1="{x}" y1="{LABEL_Y + 5}" x2="{x}" y2="-1" stroke="{th["stroke"]}"/>' for x in xs
        )
        groups.append(
            f'<g class="snk-label l{i}">'
            f'<rect x="{left:.1f}" y="{LABEL_Y - 12}" width="{w:.1f}" height="17" rx="8.5" fill="{th["pill"]}" stroke="{th["stroke"]}"/>'
            f"{pointers}"
            f'<text x="{left + 8:.1f}" y="{LABEL_Y}" font-size="11" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">{"".join(tspans)}</text></g>'
        )

    style = f"<style>.snk-label{{opacity:0;animation:none {duration}ms linear infinite}}{''.join(css)}</style>"
    svg = svg.replace("</svg>", style + "".join(groups) + "</svg>")
    open(path, "w", encoding="utf-8").write(svg)
    return len(groups_ev)


def main():
    args = sys.argv[1:]
    cal, public = calendar(), public_commits()
    for path, theme in zip(args[::2], args[1::2]):
        print(path, annotate(path, theme, cal, public))


if __name__ == "__main__":
    main()
