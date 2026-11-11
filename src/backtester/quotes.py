"""Check that the `quote` of a regulatory milestone really appears in its source.

The source (HTML page or PDF) is downloaded and turned into plain text. Both the
text and the quote are normalised the same way: lower case, one space between
words, plain ASCII quotes and dashes. A milestone passes when the normalised
quote is a substring of the normalised text.

A pass does not set verified_on. It only tells the author which quotes need no
manual search; a failed or unreadable source still needs a human look.
"""

import functools
import html
import io
import re
import time

import requests
from pypdf import PdfReader

USER_AGENT = "signal-backtester/0.1 (source quote checker)"
TIMEOUT_SECONDS = 30
RETRY_WAIT_SECONDS = 15

_CHARACTER_MAP = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        " ": " ",
    }
)


def normalise(text: str) -> str:
    """Lower case, typographic quotes and dashes made plain, whitespace collapsed."""
    text = text.translate(_CHARACTER_MAP).lower()
    return re.sub(r"\s+", " ", text).strip()


def html_to_text(page: str) -> str:
    """Drop scripts, styles and tags; keep the visible text."""
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return html.unescape(page)


def pdf_to_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _get(url: str) -> requests.Response:
    """GET with one retry when the server says 'too many requests' (HTTP 429)."""
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
    if response.status_code == 429:
        time.sleep(RETRY_WAIT_SECONDS)
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response


@functools.cache  # several milestones share one source page; download it once per run
def fetch_text(url: str) -> str:
    """Download a source and return its plain text. Raises requests.RequestException."""
    response = _get(url)
    is_pdf = response.content.startswith(b"%PDF") or "pdf" in response.headers.get(
        "Content-Type", ""
    )
    if is_pdf:
        return pdf_to_text(response.content)
    return html_to_text(response.text)


def quote_status(quote: str | None, urls: list[str | None]) -> str:
    """Return 'found in <url>', 'NOT FOUND', 'unreadable: ...' or 'no quote'.

    The archived copy is tried first because it is the version the quote was taken from.
    """
    if not quote:
        return "no quote"
    errors = []
    for url in [u for u in urls if u]:
        try:
            text = fetch_text(url)
        except Exception as error:  # network error, HTTP error or broken PDF
            errors.append(type(error).__name__)
            continue
        if normalise(quote) in normalise(text):
            return f"found in {url}"
    if errors and len(errors) == len([u for u in urls if u]):
        return f"unreadable: {', '.join(errors)}"
    return "NOT FOUND"
