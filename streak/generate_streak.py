"""Build the contribution card that never resets.

The upstream streak-stats service drops the middle number back to 0 the moment a
day goes by without a contribution. This builds the same card locally, but the
middle number only ever goes up: it counts every day (or every contribution, see
STREAK_MODE) since the account was created, so a quiet day holds the number
where it was and the next commit adds one more.

Usage: python3 streak/generate_streak.py <out_dir>
Env:   GH_USER      GitHub username (required)
       STREAK_MODE  "days" (default) -> +1 per day you contributed
                    "commits"        -> +1 per contribution
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime

CALENDAR = "https://github.com/users/{user}/contributions?from={year}-01-01&to={year}-12-31"
PROFILE = "https://api.github.com/users/{user}"
STATE_URL = "https://raw.githubusercontent.com/{user}/{user}/output/streak-state.json"
STATE_FILE = "streak-state.json"
UA = {"User-Agent": "Mozilla/5.0"}

DAY_TAG = re.compile(r"<td[^>]*ContributionCalendar-day[^>]*>")
TOOLTIP = re.compile(r"<tool-tip[^>]*?for=\"(contribution-day-component-[^\"]+)\"[^>]*>([^<]*)</tool-tip>")
COUNT = re.compile(r"([\d,]+)\s+contribution")


def attr(name, tag):
    found = re.search(name + r"=\"([^\"]+)\"", tag)
    return found.group(1) if found else None


THEMES = {
    "light": {
        "background": "FFFFFF", "border": "E2E8F0", "stroke": "E2E8F0",
        "ring": "7C3AED", "fire": "10B981", "currStreakNum": "0F172A",
        "sideNums": "0F172A", "currStreakLabel": "0891B2",
        "sideLabels": "0891B2", "dates": "64748B",
    },
    "dark": {
        "background": "0A101F", "border": "1E293B", "stroke": "1E293B",
        "ring": "A78BFA", "fire": "10B981", "currStreakNum": "E2E8F0",
        "sideNums": "E2E8F0", "currStreakLabel": "22D3EE",
        "sideLabels": "22D3EE", "dates": "94A3B8",
    },
}

FLAME = (
    "M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 "
    "C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 "
    "C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z "
    "M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 "
    "C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 "
    "C 4.51 16.85 2.36 19 -0.29 19 Z"
)


def fetch(url, timeout=30):
    request = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(request, timeout=timeout).read().decode()


def contributions(user):
    """{date: count} for every day since the account was created."""
    created = json.loads(fetch(PROFILE.format(user=user)))["created_at"][:4]
    today = date.today()
    days = {}
    for year in range(int(created), today.year + 1):
        html = fetch(CALENDAR.format(user=user, year=year))
        cells = {}
        for tag in DAY_TAG.findall(html):
            cell_id, cell_date = attr("id", tag), attr("data-date", tag)
            if cell_id and cell_date:
                cells[cell_id] = cell_date
        for cell_id, text in TOOLTIP.findall(html):
            if cell_id not in cells:
                continue
            day = datetime.strptime(cells[cell_id], "%Y-%m-%d").date()
            if day > today:
                continue
            found = COUNT.match(text.strip())
            days[day] = int(found.group(1).replace(",", "")) if found else 0
    if not days:
        raise SystemExit("no contribution data returned")
    return days


def longest_run(active):
    """Longest stretch of consecutive active days, as (length, first, last)."""
    best = run = (0, None, None)
    previous = None
    for day in active:
        if previous is not None and (day - previous).days == 1:
            run = (run[0] + 1, run[1], day)
        else:
            run = (1, day, day)
        if run[0] > best[0]:
            best = run
        previous = day
    return best


def pretty(value):
    return format(value, ",")


def pretty_date(day, today):
    stamp = "{} {}".format(day.strftime("%b"), day.day)
    return stamp if day.year == today.year else "{}, {}".format(stamp, day.year)


def card(theme, counter, total, longest, labels):
    c = THEMES[theme]
    return """<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="{alt}">
  <title>{alt}</title>
  <style>
    text {{ font-family: 'Segoe UI', Ubuntu, sans-serif; }}
    .num {{ font-size: 28px; font-weight: 700; }}
    .label {{ font-size: 14px; font-weight: 700; }}
    .date {{ font-size: 12px; }}
  </style>
  <rect x="0.5" y="0.5" width="494" height="194" rx="10" fill="#{background}" stroke="#{border}"/>
  <line x1="165" y1="28" x2="165" y2="170" stroke="#{stroke}" stroke-width="1"/>
  <line x1="330" y1="28" x2="330" y2="170" stroke="#{stroke}" stroke-width="1"/>

  <g text-anchor="middle">
    <text class="num" x="82.5" y="75" fill="#{sideNums}">{total_count}</text>
    <text class="label" x="82.5" y="101" fill="#{sideLabels}">Total Contributions</text>
    <text class="date" x="82.5" y="127" fill="#{dates}">{total_range}</text>
  </g>

  <circle cx="247.5" cy="82" r="40" fill="none" stroke="#{ring}" stroke-width="5" stroke-dasharray="211.33 40" stroke-dashoffset="42.83"/>
  <g transform="translate(247.5, 31)">
    <path d="{flame}" fill="#{fire}"/>
  </g>
  <g text-anchor="middle">
    <text class="num" x="247.5" y="92" fill="#{currStreakNum}">{counter_count}</text>
    <text class="label" x="247.5" y="146" fill="#{currStreakLabel}">{counter_label}</text>
    <text class="date" x="247.5" y="166" fill="#{dates}">{counter_range}</text>
  </g>

  <g text-anchor="middle">
    <text class="num" x="412.5" y="75" fill="#{sideNums}">{longest_count}</text>
    <text class="label" x="412.5" y="101" fill="#{sideLabels}">Longest Streak</text>
    <text class="date" x="412.5" y="127" fill="#{dates}">{longest_range}</text>
  </g>
</svg>
""".format(
        flame=FLAME,
        alt=labels["alt"],
        counter_label=labels["counter"],
        counter_count=pretty(counter["count"]),
        counter_range=counter["range"],
        total_count=pretty(total["count"]),
        total_range=total["range"],
        longest_count=pretty(longest["count"]),
        longest_range=longest["range"],
        **c
    )


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "dist"
    user = os.environ["GH_USER"]
    mode = os.environ.get("STREAK_MODE", "days").strip().lower()

    days = contributions(user)
    today = date.today()
    active = sorted(day for day, count in days.items() if count > 0)
    total_count = sum(days.values())

    # The number that never goes down. Both modes are monotonic by construction,
    # but the previous value is kept on the output branch so a bad scrape or a
    # GitHub markup change cannot walk it backwards.
    count = total_count if mode == "commits" else len(active)
    label = "Total Commits" if mode == "commits" else "Current Streak"
    try:
        previous = json.loads(fetch(STATE_URL.format(user=user), timeout=15))
        if previous.get("mode") == mode:
            count = max(count, int(previous.get("count", 0)))
    except (urllib.error.URLError, ValueError, KeyError, TypeError):
        pass

    first = active[0] if active else today
    last = active[-1] if active else today
    run, run_start, run_end = longest_run(active)
    since = "{} - Present".format(pretty_date(first, today)) if active else pretty_date(today, today)

    counter = {"count": count, "range": since}
    total = {"count": total_count, "range": since}
    longest = {
        "count": run,
        "range": "{} - {}".format(pretty_date(run_start, today), pretty_date(run_end, today))
        if run else pretty_date(today, today),
    }

    os.makedirs(out_dir, exist_ok=True)
    labels = {"counter": label, "alt": "{} {} for {}".format(pretty(count), label.lower(), user)}
    for theme in THEMES:
        name = "streak-stats.svg" if theme == "light" else "streak-stats-dark.svg"
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as handle:
            handle.write(card(theme, counter, total, longest, labels))

    with open(os.path.join(out_dir, STATE_FILE), "w", encoding="utf-8") as handle:
        json.dump({
            "mode": mode,
            "count": count,
            "updated": today.isoformat(),
            "last_active": last.isoformat() if active else None,
        }, handle, indent=2)

    print("{}: {} ({}) | total {} | longest {} | last active {}".format(
        label, count, mode, total_count, run, last))


if __name__ == "__main__":
    main()
