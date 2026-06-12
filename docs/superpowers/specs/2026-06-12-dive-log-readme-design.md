# Dive Log Profile README — Design Spec

**Date:** 2026-06-12
**Target:** `HrishiKabra/HrishiKabra` GitHub profile README (built locally in this repo, pushed by Hrishi)

## Concept

The README reads top-to-bottom as a single scuba dive. Every section is a depth;
accent colors darken as the reader scrolls (ocean palette: `#e0f7fa` → `#80deea` →
`#26c6da` → `#0097a7` → `#006064` → abyss `#041c26`). Dark mode renders the whole
page as a **night dive** (deep navy `#0d2137`-family palette, teal bioluminescent
accents) via `<picture>`/`prefers-color-scheme` on every visual asset.

No F1 theming anywhere. F1 appears only as factual content (project names in The
Reef, hobby mention in Safety Stop).

## Page structure

| Depth | Section | Content |
|---|---|---|
| — | Animated header | Custom SVG: surface scene, name half-submerged, manta silhouette, rising bubbles. Night-dive variant for dark mode. |
| — | Typing line + badges | `readme-typing-svg` cycling role lines; contact badges (email, LinkedIn, portfolio, resume) in ocean palette. |
| 0m | Surface Interval | About me + "right now" bullets (Louisa AI, TUDAI, TA, recruiting Summer 2027). |
| 🧭 | Dive Plan | Mermaid `gitGraph` career timeline: `main` = Tulane; branches `industry`, `research`, `teaching` merging in; AAMAS merge tagged. |
| 18m | The Reef | 6 featured project cards: F1 Rule Interpreter, World Cup Engine, Optimal Voting, Arbitrage Engine, FishID, Circuit DNA. |
| 30m | The Research Station | AAMAS 2026 paper, optimal-voting PyPI package, live demo link, skills summary. |
| 40m | The Wreck | Compact list of older projects: Wikipedia Race, Ocean Jukebox, ReefGuardian, GigPilot. |
| 60m | The Abyss | GitHub activity: Dive Computer card, Dive Forecast card, eel snake, 3D contribution terrain, metrics isocalendar, ocean-themed stats cards. |
| 5m | Safety Stop | Outside tech (scuba/videography, F1 fandom, Wordle), surfacing sign-off. |

Wave-shaped SVG dividers between all sections, stepping down the palette with depth.

## Custom generated cards

Two daily-generated SVG "instruments" sharing one visual system (same template
style, typography, palette — two screens of one dive console).

### Dive Computer (`scripts/dive_computer.py`)

GitHub API → dive-computer-face SVG (light + dark variants):

| Readout | Metric |
|---|---|
| BOTTOM TIME | commits in last 30 days |
| NDL | current contribution streak (days) |
| GAS MIX | top languages by % (e.g. `PY 71 / TS 18 / O₂ 11`) |
| MAX DEPTH | total contributions this calendar year |
| DECO STOP | open PRs awaiting review |

### Dive Forecast (`scripts/forecast.py`)

Probabilities about Hrishi's own activity, styled as a dive-conditions forecast
(NOT finance/order-book styling):

- "Python commit tomorrow" — % from last 100 commits' language frequency
- "New repo this month" — % from monthly repo-creation history
- "Night dive (post-midnight commit this week)" — % from commit timestamps
- "Streak survives the weekend" — % from historical weekend activity

Pricing: simple frequency estimates with Laplace smoothing. Each forecast
resolves at period end; resolutions append to `markets-history.json`; card
footer shows running **Brier score** with a methodology footnote link.

This card is intentionally removable: one `<img>` line in the README.

## Infrastructure

```
HrishiKabra/HrishiKabra
├── README.md
├── assets/                    # static SVGs: header (day/night), wave dividers
├── scripts/
│   ├── dive_computer.py
│   └── forecast.py            # shares SVG template style with dive_computer
├── markets-history.json
└── .github/workflows/
    ├── snake.yml              # existing eel workflow (unchanged)
    ├── daily-cards.yml        # cron daily: both scripts → push SVGs to `output` branch
    ├── 3d-contrib.yml         # yoshi389111/github-profile-3d-contrib, ocean colors
    └── metrics.yml            # lowlighter/metrics: isocalendar + languages, ocean theme
```

- Generated SVGs live on the `output` branch (same pattern as the snake);
  README references them via `raw.githubusercontent.com/.../output/...`.
- **Fail-safe:** on GitHub API error, scripts exit nonzero and the workflow
  skips the push — yesterday's card stays up; never a broken image.
- Only the built-in `GITHUB_TOKEN` is required. Scripts are plain Python
  (stdlib + `requests`) so they run in default Actions runners with one pip install.
- `github-readme-stats` cards keep custom hex params matching the depth palette
  (no named theme).

## Error handling & constraints

- Animated header uses SVG/CSS animations only (survives GitHub's camo proxy;
  no GIFs). All animation in embedded `<style>` within the SVG.
- Every visual asset ships light + dark variants wired through `<picture>`.
- Scripts must not exceed unauthenticated-feel API budgets: use the
  authenticated `GITHUB_TOKEN` (5k req/hr) and at most ~10 requests per run.
- Mermaid uses GitHub's native rendering; no theme overrides that break dark mode.

## Build order (each phase leaves README complete)

1. Skeleton README: depth structure, mermaid gitGraph, content, dividers
2. Animated header (day + night)
3. Dive Computer card + daily workflow
4. Dive Forecast card + history file
5. 3D-contrib + metrics workflows; final palette pass in both modes

## Testing

- Run card scripts locally against the real GitHub API for `HrishiKabra`;
  open generated SVGs in a browser to verify rendering and animation.
- Preview README rendering (light + dark) before hand-off.
- Workflow YAML validated; cron + `workflow_dispatch` triggers on all workflows
  so Hrishi can smoke-test from the Actions tab after pushing.
