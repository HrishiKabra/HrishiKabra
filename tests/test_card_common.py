from scripts.card_common import PALETTES, esc, bar, card


def test_palettes_have_required_tokens():
    for mode in ("day", "night"):
        for token in ("depth0", "depth2", "depth4", "abyss", "accent", "text", "bg"):
            assert PALETTES[mode][token].startswith("#")


def test_esc_escapes_xml():
    assert esc("<&>") == "&lt;&amp;&gt;"


def test_bar_width_proportional():
    svg = bar(x=10, y=0, w=200, frac=0.5, palette=PALETTES["day"])
    assert 'width="100"' in svg


def test_bar_clamps_frac():
    assert 'width="200"' in bar(x=0, y=0, w=200, frac=1.7, palette=PALETTES["day"])


def test_card_wraps_rows_in_svg():
    out = card(title="DIVE COMPUTER", rows_svg="<g/>", palette=PALETTES["day"], width=420, height=240)
    assert out.startswith("<svg") and "DIVE COMPUTER" in out and out.rstrip().endswith("</svg>")
