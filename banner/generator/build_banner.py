# builds banner/dark.svg and banner/light.svg from the .npy files in banner/data
# run portrait.py and logos.py first

from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import ot
from scipy.cluster.vq import kmeans2

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

HANDLE = "abhayvikyathofficial"
ROWS = [
    ("Name", "Abhay Vikyath"),
    ("Role", "Content & Creative Strategist"),
    ("Location", "Bengaluru, Karnataka, India"),
    ("Status", "Building + Creating + Learning + Shipping"),
    ("Toolkit", "Figma, Photoshop, Premiere Pro, After Effects"),
    ("Languages", "HTML5, CSS3, JavaScript, TypeScript, Python"),
    ("Frontend", "HTML5, CSS3, JavaScript"),
    ("Mail", "workswithabhay@gmail.com"),
    ("Portfolio", "abhayvikyath.in"),
    ("LinkedIn", "linkedin.com/in/abhayvikyath"),
    ("GitHub", "github.com/abhayvikyathofficial"),
]
LOGO_ORDER = ["figma", "photoshop", "flipstudio"]

THEMES = {
    "dark": dict(
        bg="#0A101F",
        window="#0A101F",
        titlebar="#0E1628",
        portrait="#A78BFA",
        chrome="#22D3EE",
        accent="#10B981",
        text="#E2E8F0",
        muted="#64748B",
        leader="#334155",
        frame="#22D3EE",
        pill_text="#0A101F",
    ),
    "light": dict(
        bg="#FFFFFF",
        window="#FFFFFF",
        titlebar="#F1F5F9",
        portrait="#7C3AED",
        chrome="#0891B2",
        accent="#10B981",
        text="#0F172A",
        muted="#64748B",
        leader="#CBD5E1",
        frame="#0891B2",
        pill_text="#FFFFFF",
    ),
}

W, H = 1180, 610
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
CHAR_W = 0.6

WIN_X, WIN_Y, WIN_W, WIN_H = 10, 10, 1160, 590
TITLE_H = 40

PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 30, 66, 448, 516
CELL = 1.4
GRID_W, GRID_H = 300, 340
PORTRAIT_X = PANEL_X + (PANEL_W - GRID_W * CELL) / 2
PORTRAIT_Y = PANEL_Y + 30

INFO_X, INFO_R = 520, 1140
ROW_FS, HEAD_FS, LIVE_FS, PILL_FS = 14, 13, 12, 14
ROW_STEP = 23

INTRO_GROUPS = 60
INTRO_SPAN = 2.0
INTRO_FADE = 0.45
INTRO_END = 3.2
INTRO_MAX_SEGMENT = {"dark": 1, "light": 2}
INTRO_BLOCK = 24

HOLD_PORTRAIT = 3.0
HOLD_LOGO = 2.0
TRANSITION = 1.3

DRIFT_BANDS = 94
DRIFT_FRACTION = 0.42
DRIFT_NOISE_SIGMA = 4.0

TRAVELLERS = 900
TRAVELLER_SIZE = 2.0
LOGO_SIZE = 200
LOGO_CENTRE = (GRID_W / 2, GRID_H / 2 - 6)

EASE = "0.45 0 0.55 1"
RNG_SEED = 7


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def runs_path(cells):
    # merge neighbouring dots in a row into one rect
    if len(cells) == 0:
        return ""
    order = np.lexsort((cells[:, 1], cells[:, 0]))
    cells = cells[order]
    parts = []
    start = prev = None
    row = None
    for r, c in cells:
        if row == r and c == prev + 1:
            prev = c
            continue
        if row is not None:
            parts.append(f"M{start} {row}h{prev - start + 1}v1h-{prev - start + 1}z")
        row, start, prev = r, c, c
    parts.append(f"M{start} {row}h{prev - start + 1}v1h-{prev - start + 1}z")
    return "".join(parts)


def text_locked(x, y, s, size, fill, anchor="start", weight="400", extra=""):
    length = len(s) * size * CHAR_W
    return (
        f'<text x="{fmt(x)}" y="{fmt(y)}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
        f'font-weight="{weight}" textLength="{fmt(length)}" lengthAdjust="spacingAndGlyphs"{extra}>'
        f"{escape(s)}</text>"
    )


def spline_attrs(n):
    return f'calcMode="spline" keySplines="{";".join([EASE] * n)}"'


def build_timeline(n_logos):
    t = [0.0, HOLD_PORTRAIT]
    for i in range(n_logos):
        t.append(t[-1] + TRANSITION)
        t.append(t[-1] + HOLD_LOGO)
    t.append(t[-1] + TRANSITION)
    return t, t[-1]


def intro_groups(cells, rng, max_segment):
    # split rows into short random pieces and spread them over the groups
    # block by block, so the fade in looks even instead of patchy
    order = np.lexsort((cells[:, 1], cells[:, 0]))
    c = cells[order]
    seg_id = np.zeros(len(c), dtype=np.int64)
    sid, left = -1, 0
    for i in range(len(c)):
        new_run = i == 0 or c[i, 0] != c[i - 1, 0] or c[i, 1] != c[i - 1, 1] + 1
        if new_run or left == 0:
            sid += 1
            left = int(rng.integers(1, max_segment + 1))
        seg_id[i] = sid
        left -= 1
    n_seg = sid + 1
    first = np.searchsorted(seg_id, np.arange(n_seg))
    block = (c[first, 0] // INTRO_BLOCK) * 1000 + (c[first, 1] // INTRO_BLOCK)
    seg_group = np.empty(n_seg, dtype=np.int64)
    for b in np.unique(block):
        idx = np.where(block == b)[0]
        idx = idx[rng.permutation(len(idx))]
        seg_group[idx] = (np.arange(len(idx)) + int(rng.integers(INTRO_GROUPS))) % INTRO_GROUPS
    group = np.empty(len(cells), dtype=np.int64)
    group[order] = seg_group[seg_id]
    return group


def drift_bands(cells, rng, noise_sigma):
    pos = cells[:, ::-1].astype(np.float64) + 0.5
    noisy = pos + rng.normal(0, noise_sigma, pos.shape)
    init = noisy[rng.choice(len(noisy), DRIFT_BANDS, replace=False)]
    _, label = kmeans2(noisy, init, iter=25, minit="matrix", seed=RNG_SEED)
    return label


def logo_points(name, n, rng):
    mask = np.load(DATA / f"logo_{name}.npy")
    ys, xs = np.where(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    scale = LOGO_SIZE / max(x1 - x0 + 1, y1 - y0 + 1)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pts = np.stack([(xs - cx) * scale + LOGO_CENTRE[0], (ys - cy) * scale + LOGO_CENTRE[1]], 1)
    pick = pts[rng.choice(len(pts), min(len(pts), 40000), replace=False)]
    init = pick[rng.choice(len(pick), n, replace=False)]
    centres, _ = kmeans2(pick, init, iter=20, minit="matrix", seed=RNG_SEED)
    return centres


def portrait_points(cells, n, rng):
    pos = cells[:, ::-1].astype(np.float64) + 0.5
    pick = pos[rng.choice(len(pos), min(len(pos), 40000), replace=False)]
    init = pick[rng.choice(len(pick), n, replace=False)]
    centres, _ = kmeans2(pick, init, iter=20, minit="matrix", seed=RNG_SEED)
    return centres


def ot_match(a, b):
    cost = ot.dist(a, b, metric="sqeuclidean")
    plan = ot.emd(np.full(len(a), 1 / len(a)), np.full(len(b), 1 / len(b)), cost, numItermax=2_000_000)
    return plan.argmax(1)


def build(theme_name, logos):
    th = THEMES[theme_name]
    rng = np.random.default_rng(RNG_SEED)
    dots = np.load(DATA / f"dots_{theme_name}.npy")
    cells = np.argwhere(dots)

    key_t, total = build_timeline(len(logos))
    key_times = ";".join(fmt(t / total) for t in key_t)
    begin_loop = f"{INTRO_END}s"
    out = []
    a = out.append

    a(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" role="img" aria-label="Abhay Vikyath - Content &amp; Creative Strategist">'
    )
    a(f"<title>Abhay Vikyath - Content &amp; Creative Strategist</title>")

    # window
    a(f'<rect x="{WIN_X}" y="{WIN_Y}" width="{WIN_W}" height="{WIN_H}" rx="14" fill="{th["window"]}" stroke="{th["chrome"]}" stroke-opacity="0.35"/>')
    a(f'<path d="M{WIN_X} {WIN_Y + 14}a14 14 0 0 1 14-14h{WIN_W - 28}a14 14 0 0 1 14 14v{TITLE_H - 14}h-{WIN_W}z" fill="{th["titlebar"]}"/>')
    a(f'<line x1="{WIN_X}" y1="{WIN_Y + TITLE_H}" x2="{WIN_X + WIN_W}" y2="{WIN_Y + TITLE_H}" stroke="{th["chrome"]}" stroke-opacity="0.25"/>')
    for i in range(3):
        a(f'<circle cx="{WIN_X + 24 + i * 18}" cy="{WIN_Y + TITLE_H / 2}" r="5" fill="none" stroke="{th["chrome"]}" stroke-opacity="0.55"/>')
    a(text_locked(W / 2, WIN_Y + TITLE_H / 2 + 5, "profile.sh --live", 13, th["muted"], anchor="middle"))

    a(f'<rect x="{PANEL_X}" y="{PANEL_Y}" width="{PANEL_W}" height="{PANEL_H}" rx="8" fill="none" stroke="{th["frame"]}" stroke-opacity="0.22"/>')
    a(text_locked(PANEL_X + 14, PANEL_Y + 20, "VISUAL.MAP", HEAD_FS, th["chrome"], weight="600"))

    tf = f'transform="translate({fmt(PORTRAIT_X)} {fmt(PORTRAIT_Y)}) scale({CELL})"'

    # intro fade in
    group = intro_groups(cells, rng, INTRO_MAX_SEGMENT[theme_name])
    begins = rng.permutation(np.linspace(0, INTRO_SPAN - INTRO_FADE, INTRO_GROUPS)) + 0.15
    a(f'<g {tf} fill="{th["portrait"]}" shape-rendering="crispEdges">')
    a(f'<set attributeName="visibility" to="hidden" begin="{INTRO_END}s" fill="freeze"/>')
    for g in range(INTRO_GROUPS):
        d = runs_path(cells[group == g])
        if not d:
            continue
        a(
            f'<path opacity="0" d="{d}"><animate attributeName="opacity" from="0" to="1" '
            f'begin="{fmt(begins[g])}s" dur="{INTRO_FADE}s" fill="freeze"/></path>'
        )
    a("</g>")

    # portrait that drifts out when the logos come in
    centre = np.array(LOGO_CENTRE)
    label = drift_bands(cells, rng, DRIFT_NOISE_SIGMA)
    n_seg = len(key_t) - 1
    a(f'<g {tf} fill="{th["portrait"]}" shape-rendering="crispEdges" visibility="hidden">')
    a(f'<set attributeName="visibility" to="visible" begin="{INTRO_END}s" fill="freeze"/>')
    for b in range(DRIFT_BANDS):
        sel = cells[label == b]
        if len(sel) == 0:
            continue
        centroid = sel[:, ::-1].mean(0) + 0.5
        dx, dy = DRIFT_FRACTION * (centre - centroid)
        move, still = f"{fmt(dx)} {fmt(dy)}", "0 0"
        tr_vals = [still, still] + [move] * (len(key_t) - 3) + [still]
        op_vals = ["1", "1"] + ["0"] * (len(key_t) - 3) + ["1"]
        a(
            f'<path d="{runs_path(sel)}">'
            f'<animateTransform attributeName="transform" type="translate" values="{";".join(tr_vals)}" '
            f'keyTimes="{key_times}" {spline_attrs(n_seg)} dur="{fmt(total)}s" begin="{begin_loop}" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{";".join(op_vals)}" keyTimes="{key_times}" '
            f'{spline_attrs(n_seg)} dur="{fmt(total)}s" begin="{begin_loop}" repeatCount="indefinite"/>'
            f"</path>"
        )
    a("</g>")

    # dots that move between the logos
    if logos:
        start = portrait_points(cells, TRAVELLERS, rng)
        sets = [logo_points(n, TRAVELLERS, rng) for n in logos]
        paths = [start]
        cur = start
        for s in sets:
            cur = s[ot_match(cur, s)]
            paths.append(cur)

        op = ["0", "0"]
        for _ in logos:
            op += ["1", "1"]
        op.append("0")
        a(f'<g {tf} fill="{th["portrait"]}" shape-rendering="crispEdges" opacity="0">')
        a(
            f'<animate attributeName="opacity" values="{";".join(op)}" keyTimes="{key_times}" '
            f'{spline_attrs(n_seg)} dur="{fmt(total)}s" begin="{begin_loop}" repeatCount="indefinite"/>'
        )
        half = TRAVELLER_SIZE / 2
        f1 = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
        for i in range(TRAVELLERS):
            p0 = f"{f1(paths[0][i, 0])} {f1(paths[0][i, 1])}"
            vals = [p0, p0]
            for k in range(1, len(paths)):
                pk = f"{f1(paths[k][i, 0])} {f1(paths[k][i, 1])}"
                vals += [pk, pk]
            vals.append(p0)
            a(
                f'<rect x="-{fmt(half)}" y="-{fmt(half)}" width="{TRAVELLER_SIZE}" height="{TRAVELLER_SIZE}">'
                f'<animateTransform attributeName="transform" type="translate" values="{";".join(vals)}" '
                f'keyTimes="{key_times}" {spline_attrs(n_seg)} dur="{fmt(total)}s" begin="{begin_loop}" repeatCount="indefinite"/>'
                f"</rect>"
            )
        a("</g>")

    # info panel
    info_w = INFO_R - INFO_X
    block_h = 34 + len(ROWS) * ROW_STEP + 58
    top = PANEL_Y + (PANEL_H - block_h) / 2 + 14
    a(text_locked(INFO_X, top, "SYSTEM.INFO", HEAD_FS, th["chrome"], weight="600"))
    live_w = 58
    lx = INFO_R - live_w
    a(f'<rect x="{lx}" y="{top - 14}" width="{live_w}" height="20" rx="10" fill="#EF4444" fill-opacity="0.12" stroke="#EF4444" stroke-opacity="0.6"/>')
    a(
        f'<circle cx="{lx + 13}" cy="{top - 4}" r="4" fill="#EF4444">'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>'
    )
    a(text_locked(lx + 23, top, "LIVE", LIVE_FS, "#EF4444", weight="700"))
    a(f'<line x1="{INFO_X}" y1="{top + 10}" x2="{INFO_R}" y2="{top + 10}" stroke="{th["chrome"]}" stroke-opacity="0.2"/>')

    total_chars = int(info_w // (ROW_FS * CHAR_W))
    y = top + 34
    for label_txt, value in ROWS:
        n_lead = total_chars - len(label_txt) - len(value) - 2
        if n_lead < 3:
            raise ValueError(f"row too long: {label_txt} = {value}")
        a(text_locked(INFO_X, y, label_txt, ROW_FS, th["chrome"]))
        lead_x = INFO_X + (len(label_txt) + 1) * ROW_FS * CHAR_W
        a(text_locked(lead_x, y, "." * n_lead, ROW_FS, th["leader"]))
        a(text_locked(INFO_R, y, value, ROW_FS, th["text"], anchor="end"))
        y += ROW_STEP

    pill = f"@{HANDLE}"
    pill_w = len(pill) * PILL_FS * CHAR_W + 28
    py = y + 14
    a(f'<rect x="{INFO_X}" y="{py}" width="{fmt(pill_w)}" height="28" rx="14" fill="{th["accent"]}"/>')
    a(text_locked(INFO_X + 14, py + 19, pill, PILL_FS, th["pill_text"], weight="700"))

    a("</svg>")
    return "".join(out)


def main():
    logos = [n for n in LOGO_ORDER if (DATA / f"logo_{n}.npy").exists()]
    for theme in ("dark", "light"):
        path = ROOT / f"{theme}.svg"
        path.write_text(build(theme, logos), encoding="utf-8")
        print(theme, path.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
