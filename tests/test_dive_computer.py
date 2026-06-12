from scripts.dive_computer import current_streak, gas_mix, render


def test_current_streak_counts_back_from_today():
    days = {"2026-06-12": 3, "2026-06-11": 1, "2026-06-10": 0, "2026-06-09": 5}
    assert current_streak(days, today="2026-06-12") == 2


def test_current_streak_allows_empty_today():
    days = {"2026-06-12": 0, "2026-06-11": 2, "2026-06-10": 1}
    assert current_streak(days, today="2026-06-12") == 2


def test_current_streak_zero_when_cold():
    days = {"2026-06-12": 0, "2026-06-11": 0, "2026-06-10": 1}
    assert current_streak(days, today="2026-06-12") == 0


def test_gas_mix_top2_with_o2_remainder():
    langs = ["Python"] * 7 + ["TypeScript"] * 2 + ["R"] * 1
    assert gas_mix(langs) == "PY 70 / TS 20 / O₂ 10"


def test_gas_mix_empty():
    assert gas_mix([]) == "AIR 100"


def test_render_contains_metrics():
    svg = render(mode="day", bottom_time=42, ndl=7, mix="PY 70 / TS 20 / O₂ 10", max_depth=812, deco=2)
    assert "42" in svg and "BOTTOM TIME" in svg and svg.startswith("<svg")
