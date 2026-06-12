# Dive Forecast — methodology

The Dive Forecast card on my profile prices four daily "markets" about my own
GitHub activity, then scores its own calibration. This page is the fine print.

## The markets

| Market | Question | Resolves |
|---|---|---|
| `python-commit` | Will tomorrow include a push to a Python repo? | Next day |
| `new-repo-month` | Will I create a new repository this calendar month? | Last day of month |
| `night-dive-week` | Will this ISO week include a push between 00:00–05:00 America/Chicago? | Sunday |
| `weekend-streak` | Will I contribute on both Saturday and Sunday? | Sunday |

## Pricing

Probabilities are frequency estimates over my recent public activity
(push events, repo creation dates, and the contribution calendar), with
**Laplace smoothing**:

```
p = (hits + 1) / (n + 2)
```

so an empty history prices at 50% rather than a false certainty. Examples:
`python-commit` is the smoothed share of my recent pushes that hit Python
repos; `weekend-streak` is the smoothed share of recent weekends (up to 26)
with contributions on both days.

## Resolution & scoring

Each day's forecasts are appended to `markets-history.json` (kept on the
`output` branch). Every run resolves any forecast whose horizon has passed,
using the same data sources. Forecasts whose evidence has aged out of the
90-day events window stay unresolved and are excluded from scoring.

Calibration is the running **Brier score** over all resolved forecasts:

```
B = mean over resolved of (p − outcome)²   where outcome ∈ {0, 1}
```

Lower is better; 0.25 is the score of always guessing 50%. The card footer
shows the current score and sample size.

## Honesty notes

- A push event's "language" is its repo's primary language — a Python commit
  to a mixed repo counts as whatever GitHub labels the repo.
- Only public activity is visible to the generator, so private-repo work
  undercounts everything except the contribution calendar.
- Generated nightly by `scripts/forecast.py`; pure logic is unit-tested,
  and a fetch failure keeps the previous card rather than publishing garbage.
