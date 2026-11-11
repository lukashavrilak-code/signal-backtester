"""The quote check finds a quote despite layout differences and reports a missing one.

No network: fetch_text is replaced by a fake that returns a fixed page.
"""

from backtester import quotes

PAGE = """<html><head><style>p {color: red}</style><script>var x = "6 June 2025";</script></head>
<body><p>Safety&nbsp;Announcement</p><p>[ 05-15-2015 ]
Safety   Announcement</p><p>PRAC meeting 2\u20135 June 2025</p></body></html>"""


def fake_fetch(url: str) -> str:
    if url == "http://broken":
        raise ConnectionError("no network")
    return quotes.html_to_text(PAGE)


def test_normalise_collapses_whitespace_case_and_typography():
    assert quotes.normalise("  PRAC\u00a0Meeting 2\u20135\n June ") == "prac meeting 2-5 june"


def test_html_to_text_drops_scripts_and_tags():
    text = quotes.html_to_text(PAGE)
    assert "color: red" not in text
    assert "var x" not in text
    assert "Safety" in text


def test_quote_found_despite_line_breaks_and_dashes(monkeypatch):
    monkeypatch.setattr(quotes, "fetch_text", fake_fetch)
    assert quotes.quote_status("[ 05-15-2015 ] Safety Announcement", ["http://a"]).startswith(
        "found"
    )
    assert quotes.quote_status("PRAC meeting 2-5 June 2025", ["http://a"]).startswith("found")


def test_text_inside_a_script_does_not_count(monkeypatch):
    monkeypatch.setattr(quotes, "fetch_text", fake_fetch)
    assert quotes.quote_status("6 June 2025", ["http://a"]) == "NOT FOUND"


def test_unreadable_source_is_reported_and_the_next_url_is_tried(monkeypatch):
    monkeypatch.setattr(quotes, "fetch_text", fake_fetch)
    assert quotes.quote_status("x", ["http://broken"]).startswith("unreadable")
    assert quotes.quote_status("Safety Announcement", ["http://broken", "http://a"]).startswith(
        "found"
    )


def test_missing_quote_is_not_an_error():
    assert quotes.quote_status(None, ["http://a"]) == "no quote"
