"""Render the Dive Computer card from live GitHub activity.

Readouts: BOTTOM TIME (commits, 30d), NDL (streak), GAS MIX (languages),
MAX DEPTH (contributions this year), DECO STOP (open PRs).

Pure logic is kept separate from fetching so it is unit-testable offline.
Exits nonzero on any fetch error so the publish step keeps yesterday's card.
"""

import datetime as dt
import json
import os
import sys
import urllib.request
from collections import Counter

from scripts.card_common import MONO, PALETTES, bar, card, esc

API = "https://api.github.com"

LANG_ABBREV = {
    "Python": "PY",
    "TypeScript": "TS",
    "JavaScript": "JS",
    "Java": "JV",
    "C++": "C++",
    "Jupyter Notebook": "NB",
    "HTML": "HT",
    "R": "R",
}


def _get(url, token, payload=None):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "dive-instruments",
    })
    if payload is not None:
        req.data = json.dumps(payload).encode()
        req.method = "POST"
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch(token, user):
    calendar_query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }"""
    gql = _get(f"{API}/graphql", token, {"query": calendar_query, "variables": {"login": user}})
    cal = gql["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = {d["date"]: d["contributionCount"]
            for w in cal["weeks"] for d in w["contributionDays"]}

    repos = _get(f"{API}/users/{user}/repos?sort=pushed&per_page=100", token)
    langs = [r["language"] for r in repos if not r["fork"] and r["language"]]

    prs = _get(f"{API}/search/issues?q=author:{user}+type:pr+state:open", token)
    events = _get(f"{API}/users/{user}/events?per_page=100", token)

    return {
        "days": days,
        "year_total": cal["totalContributions"],
        "langs": langs,
        "open_prs": prs["total_count"],
        "events": events,
    }


def commits_last_30d(events, today):
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=30)).isoformat()
    return sum(e["payload"].get("size", 0) for e in events
               if e["type"] == "PushEvent" and e["created_at"][:10] >= cutoff)


def current_streak(days, today):
    d = dt.date.fromisoformat(today)
    if days.get(d.isoformat(), 0) == 0:
        d -= dt.timedelta(days=1)  # an empty today doesn't break the streak yet
    streak = 0
    while days.get(d.isoformat(), 0) > 0:
        streak += 1
        d -= dt.timedelta(days=1)
    return streak


def gas_mix(langs):
    if not langs:
        return "AIR 100"
    counts = Counter(langs)
    n = sum(counts.values())
    top = counts.most_common(2)
    parts, used = [], 0
    for lang, c in top:
        pct = round(c / n * 100)
        abbrev = LANG_ABBREV.get(lang, lang[:2].upper())
        parts.append(f"{abbrev} {pct}")
        used += pct
    if used < 100:
        parts.append(f"O₂ {100 - used}")
    return " / ".join(parts)


def _row(y, label, value_svg, palette):
    return (
        f'<text x="24" y="{y}" font-family="{MONO}" font-size="12" letter-spacing="2" '
        f'fill="{palette["depth3"]}">{esc(label)}</text>'
        f'<text x="396" y="{y}" text-anchor="end" font-family="{MONO}" font-size="15" '
        f'fill="{palette["text"]}">{value_svg}</text>'
    )


def render(mode, bottom_time, ndl, mix, max_depth, deco, synced=""):
    p = PALETTES[mode]

    def val(strong, faint=""):
        out = f'<tspan font-weight="700" fill="{p["accent"]}">{esc(strong)}</tspan>'
        if faint:
            out += f'<tspan font-size="12" fill="{p["depth3"]}"> {esc(faint)}</tspan>'
        return out

    rows = "".join([
        _row(86, "BOTTOM TIME", val(bottom_time, "commits · 30d"), p),
        _row(118, "NDL", val(ndl, "day streak"), p),
        _row(150, "GAS MIX", val(mix), p),
        _row(182, "MAX DEPTH", val(max_depth, "contributions · 1y"), p),
        _row(214, "DECO STOP", val(deco, "open PRs"), p),
    ])
    footer = (
        f'<text x="396" y="34" text-anchor="end" font-family="{MONO}" font-size="10" '
        f'fill="{p["depth2"]}">{esc(synced)}</text>'
    )
    return card(title="DIVE COMPUTER", rows_svg=rows, palette=p, width=420, height=240,
                footer_svg=footer)


def main():
    token = os.environ["GITHUB_TOKEN"]
    user = os.environ.get("GH_USER", "HrishiKabra")
    today = dt.date.today().isoformat()
    data = fetch(token, user)

    metrics = {
        "bottom_time": commits_last_30d(data["events"], today),
        "ndl": current_streak(data["days"], today),
        "mix": gas_mix(data["langs"]),
        "max_depth": data["year_total"],
        "deco": data["open_prs"],
        "synced": f"sync {today}",
    }
    os.makedirs("dist", exist_ok=True)
    for mode, name in (("day", "dist/dive-computer.svg"), ("night", "dist/dive-computer-dark.svg")):
        with open(name, "w") as f:
            f.write(render(mode=mode, **metrics))
    print(f"wrote dive computer cards: {metrics}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail-safe: keep yesterday's card on any error
        print(f"dive_computer failed: {e}", file=sys.stderr)
        sys.exit(1)
