"""Render the Dive Forecast card: Brier-scored probabilities about my own activity.

Four markets, priced daily from observed frequencies (Laplace-smoothed), each
resolving at its horizon. Resolved outcomes accumulate in markets-history.json
(persisted on the output branch) and the card footer shows running calibration.
Methodology: docs/FORECAST.md. Exits nonzero on fetch error (fail-safe).
"""

import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

from scripts.card_common import MONO, PALETTES, bar, card, esc
from scripts.dive_computer import API, _get

LOCAL_TZ = ZoneInfo("America/Chicago")

LABELS = {
    "python-commit": "Python commit tomorrow",
    "new-repo-month": "New repo this month",
    "night-dive-week": "Night dive this week (00–05h commit)",
    "weekend-streak": "Streak survives the weekend",
}


# ---------- pure probability / scoring layer ----------

def laplace(hits, n):
    return (hits + 1) / (n + 2)


def brier(history):
    resolved = [e for e in history if e.get("outcome") is not None]
    if not resolved:
        return None
    return sum((e["p"] - (1.0 if e["outcome"] else 0.0)) ** 2 for e in resolved) / len(resolved)


def resolve_due(history, today, resolvers):
    for e in history:
        if e.get("outcome") is None and e["horizon"] < today:
            resolver = resolvers.get(e["market"])
            if resolver is not None:
                e["outcome"] = resolver(e)
    return history


def horizons(today):
    d = dt.date.fromisoformat(today)
    next_month = (d.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
    sunday = d + dt.timedelta(days=6 - d.weekday())
    return {
        "python-commit": (d + dt.timedelta(days=1)).isoformat(),
        "new-repo-month": (next_month - dt.timedelta(days=1)).isoformat(),
        "night-dive-week": sunday.isoformat(),
        "weekend-streak": sunday.isoformat(),
    }


def todays_forecasts(probs, today, existing):
    seen = {e["id"] for e in existing}
    hz = horizons(today)
    out = []
    for market, p in probs.items():
        entry_id = f"{market}:{today}"
        if entry_id in seen:
            continue
        out.append({
            "id": entry_id,
            "market": market,
            "date": today,
            "horizon": hz[market],
            "p": round(p, 3),
            "outcome": None,
        })
    return out


# ---------- data-derived probabilities ----------

def _push_dates_and_langs(events, repo_langs):
    pushes = []
    for e in events:
        if e["type"] != "PushEvent":
            continue
        ts = dt.datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))
        local = ts.astimezone(LOCAL_TZ)
        lang = repo_langs.get(e["repo"]["name"].split("/")[-1])
        pushes.append({"local": local, "lang": lang})
    return pushes


def probabilities(pushes, repos, days, today):
    d = dt.date.fromisoformat(today)

    python_pushes = sum(1 for p in pushes if p["lang"] == "Python")
    p_python = laplace(python_pushes, len(pushes))

    year_ago = d - dt.timedelta(days=365)
    creation_months = {r["created_at"][:7] for r in repos
                       if r["created_at"][:10] >= year_ago.isoformat()}
    p_repo = laplace(len(creation_months), 12)

    weeks_seen, night_weeks = set(), set()
    for p in pushes:
        wk = p["local"].date().isocalendar()[:2]
        weeks_seen.add(wk)
        if p["local"].hour < 5:
            night_weeks.add(wk)
    p_night = laplace(len(night_weeks), len(weeks_seen))

    weekends = both_days = 0
    sat = d - dt.timedelta(days=d.weekday() + 2)  # most recent completed Saturday
    while sat.isoformat() in days and weekends < 26:
        sun = sat + dt.timedelta(days=1)
        if sun >= d:
            break
        weekends += 1
        if days.get(sat.isoformat(), 0) > 0 and days.get(sun.isoformat(), 0) > 0:
            both_days += 1
        sat -= dt.timedelta(days=7)
    p_weekend = laplace(both_days, weekends)

    return {
        "python-commit": p_python,
        "new-repo-month": p_repo,
        "night-dive-week": p_night,
        "weekend-streak": p_weekend,
    }


def build_resolvers(pushes, repos, days):
    earliest = min((p["local"].date().isoformat() for p in pushes), default="9999-12-31")

    def python_commit(e):
        if e["horizon"] < earliest:
            return None  # events window no longer covers this day
        return any(p["local"].date().isoformat() == e["horizon"] and p["lang"] == "Python"
                   for p in pushes)

    def new_repo_month(e):
        month = e["horizon"][:7]
        return any(r["created_at"][:7] == month for r in repos)

    def night_dive_week(e):
        if e["horizon"] < earliest:
            return None
        wk = dt.date.fromisoformat(e["horizon"]).isocalendar()[:2]
        return any(p["local"].date().isocalendar()[:2] == wk and p["local"].hour < 5
                   for p in pushes)

    def weekend_streak(e):
        sun = dt.date.fromisoformat(e["horizon"])
        sat = sun - dt.timedelta(days=1)
        if sat.isoformat() not in days:
            return None
        return days.get(sat.isoformat(), 0) > 0 and days.get(sun.isoformat(), 0) > 0

    return {
        "python-commit": python_commit,
        "new-repo-month": new_repo_month,
        "night-dive-week": night_dive_week,
        "weekend-streak": weekend_streak,
    }


# ---------- rendering ----------

def render(mode, probs, brier_score, n_resolved, synced=""):
    p = PALETTES[mode]
    rows = []
    y = 78
    for market in ("python-commit", "new-repo-month", "night-dive-week", "weekend-streak"):
        prob = probs[market]
        rows.append(
            f'<text x="24" y="{y}" font-family="{MONO}" font-size="12" letter-spacing="1" '
            f'fill="{p["text"]}">{esc(LABELS[market])}</text>'
            + bar(x=24, y=y + 7, w=300, frac=prob, palette=p)
            + f'<text x="396" y="{y + 16}" text-anchor="end" font-family="{MONO}" font-size="15" '
              f'font-weight="700" fill="{p["accent"]}">{round(prob * 100)}%</text>'
        )
        y += 40
    if brier_score is None:
        calib = "calibration: collecting resolutions…"
    else:
        calib = f"calibration (Brier): {brier_score:.2f} · n={n_resolved} resolved"
    footer = (
        f'<text x="24" y="232" font-family="{MONO}" font-size="11" '
        f'fill="{p["depth3"]}">{esc(calib)} · docs/FORECAST.md</text>'
        f'<text x="396" y="34" text-anchor="end" font-family="{MONO}" font-size="10" '
        f'fill="{p["depth2"]}">{esc(synced)}</text>'
    )
    return card(title="DIVE FORECAST", rows_svg="".join(rows), palette=p, width=420, height=240,
                footer_svg=footer)


# ---------- orchestration ----------

def fetch(token, user):
    repos = _get(f"{API}/users/{user}/repos?sort=pushed&per_page=100", token)
    repos = [r for r in repos if not r["fork"]]
    events = _get(f"{API}/users/{user}/events?per_page=100", token)
    calendar_query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar { weeks { contributionDays { date contributionCount } } }
        }
      }
    }"""
    gql = _get(f"{API}/graphql", token, {"query": calendar_query, "variables": {"login": user}})
    cal = gql["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = {d["date"]: d["contributionCount"]
            for w in cal["weeks"] for d in w["contributionDays"]}
    return repos, events, days


def main():
    token = os.environ["GITHUB_TOKEN"]
    user = os.environ.get("GH_USER", "HrishiKabra")
    history_path = os.environ.get("HISTORY_PATH", "markets-history.json")
    today = dt.date.today().isoformat()

    repos, events, days = fetch(token, user)
    repo_langs = {r["name"]: r["language"] for r in repos}
    pushes = _push_dates_and_langs(events, repo_langs)

    try:
        with open(history_path) as f:
            history = json.load(f)["forecasts"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        history = []

    history = resolve_due(history, today, build_resolvers(pushes, repos, days))
    probs = probabilities(pushes, repos, days, today)
    history.extend(todays_forecasts(probs, today, existing=history))

    b = brier(history)
    n_resolved = sum(1 for e in history if e.get("outcome") is not None)

    os.makedirs("dist", exist_ok=True)
    for mode, name in (("day", "dist/forecast.svg"), ("night", "dist/forecast-dark.svg")):
        with open(name, "w") as f:
            f.write(render(mode, probs, b, n_resolved, synced=f"sync {today}"))
    with open("dist/markets-history.json", "w") as f:
        json.dump({"forecasts": history}, f, indent=1)
    print(f"wrote forecast cards: { {k: round(v, 2) for k, v in probs.items()} }, "
          f"brier={b}, resolved={n_resolved}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail-safe: keep yesterday's card on any error
        print(f"forecast failed: {e}", file=sys.stderr)
        sys.exit(1)
