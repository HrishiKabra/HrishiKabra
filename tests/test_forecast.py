from scripts.forecast import brier, laplace, resolve_due, todays_forecasts


def test_laplace_smoothing():
    assert laplace(hits=8, n=10) == (8 + 1) / (10 + 2)
    assert laplace(hits=0, n=0) == 0.5


def test_brier_mean_squared_error():
    hist = [
        {"p": 0.8, "outcome": True},
        {"p": 0.3, "outcome": False},
        {"p": 0.5, "outcome": None},
    ]
    assert abs(brier(hist) - ((0.2**2 + 0.3**2) / 2)) < 1e-9


def test_brier_none_when_nothing_resolved():
    assert brier([{"p": 0.5, "outcome": None}]) is None


def test_resolve_due_only_past_horizon():
    hist = [
        {"id": "a", "market": "python-commit", "horizon": "2026-06-10", "p": 0.8, "outcome": None},
        {"id": "b", "market": "python-commit", "horizon": "2026-06-13", "p": 0.7, "outcome": None},
    ]
    out = resolve_due(hist, today="2026-06-12", resolvers={"python-commit": lambda e: True})
    assert out[0]["outcome"] is True and out[1]["outcome"] is None


def test_resolve_due_keeps_already_resolved():
    hist = [{"id": "a", "market": "python-commit", "horizon": "2026-06-01", "p": 0.9, "outcome": False}]
    out = resolve_due(hist, today="2026-06-12", resolvers={"python-commit": lambda e: True})
    assert out[0]["outcome"] is False


def test_todays_forecasts_skips_existing_ids():
    existing = [{"id": "python-commit:2026-06-12"}]
    new = todays_forecasts(
        {"python-commit": 0.8, "new-repo-month": 0.6}, today="2026-06-12", existing=existing
    )
    assert [e["market"] for e in new] == ["new-repo-month"]
    assert new[0]["outcome"] is None and 0 < new[0]["p"] < 1
