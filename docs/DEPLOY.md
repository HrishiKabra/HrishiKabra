# Deploying the Dive Log profile

Everything in this repo is built for the **`HrishiKabra/HrishiKabra`** profile
repository. To go live:

## 1. Push the contents

Copy (or push) the following to the profile repo's default branch:

```
README.md  assets/  scripts/  tests/  conftest.py  markets-history.json
docs/FORECAST.md  .github/workflows/  .gitignore
```

## 2. Create the one required secret

`lowlighter/metrics` cannot use the built-in `GITHUB_TOKEN`. Create a
**classic PAT** at <https://github.com/settings/tokens> with scopes
`public_repo` and `read:user`, then save it in the profile repo as a secret
named **`METRICS_TOKEN`** (Settings → Secrets and variables → Actions).

The other three workflows only need the automatic `GITHUB_TOKEN` — no setup.

## 3. Prime the output branch

From the repo's **Actions** tab, run each workflow once manually
(every workflow has a `workflow_dispatch` trigger):

1. *Generate contribution snake*
2. *Generate dive instrument cards*
3. *Generate 3D contribution terrain*
4. *Generate metrics panel*

Then confirm the `output` branch contains: `snake.svg`, `snake-dark.svg`,
`dive-computer.svg`, `dive-computer-dark.svg`, `forecast.svg`,
`forecast-dark.svg`, `markets-history.json`, `3d/profile-*.svg`, `metrics.svg`.

The README's images go live as each file lands. (Until the first runs finish,
those embeds 404 — everything else renders immediately.)

## 4. Ongoing behavior

- All four workflows re-run nightly on cron; all publish with
  `keep_history: true` so they never wipe each other's files.
- The card scripts exit nonzero on any GitHub API error, which skips the
  publish step — yesterday's cards stay up rather than breaking the page.
- Forecast resolutions accumulate in `markets-history.json` on the `output`
  branch; the Brier footer appears once the first forecasts resolve
  (day two onward). Methodology: `docs/FORECAST.md`.

## Local development

```bash
python3 -m pytest                                   # unit tests (pure logic)
GITHUB_TOKEN=$(gh auth token) python3 -m scripts.dive_computer
GITHUB_TOKEN=$(gh auth token) python3 -m scripts.forecast
open dist/*.svg                                     # preview the cards
```

## Tweaks

- Remove the forecast card: delete its `<picture>` block in the README —
  nothing else depends on it.
- 3D terrain colors use the action's defaults (`season` light / `night-rainbow`
  dark); custom ocean palettes are possible via the action's `SETTING_JSON`.
- All palette hexes live in `scripts/card_common.py` and mirror the static
  assets in `assets/`.
