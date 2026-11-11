"""Check the sources of every regulatory milestone in config/studies/*.yaml.

For each milestone it reports:
  - whether the url still loads (FDA moves pages often, old ones return 404)
  - whether the `quote` really appears in the archived copy or the url (see quotes.py)
  - the Wayback Machine snapshot closest to the action date, if there is no archive_url yet
  - whether a human has confirmed the date yet (verified_on)

The check never edits the YAML files. It narrows the manual work down to the
milestones it could not confirm; the author still sets verified_on.
"""

import functools
from dataclasses import dataclass

import requests

from backtester.config import RegulatoryAction, Study
from backtester.quotes import quote_status

USER_AGENT = "signal-backtester/0.1 (source link checker)"
WAYBACK_API = "https://archive.org/wayback/available"
TIMEOUT_SECONDS = 20


@dataclass
class SourceCheck:
    study_id: str
    action: RegulatoryAction
    url_status: str  # "200", "404", "error: ...", or "no url"
    quote_status: str  # "found in <url>", "NOT FOUND", "unreadable: ...", or "no quote"
    wayback_url: str | None

    @property
    def needs_attention(self) -> bool:
        """True when a human has to look: unverified, or the quote was not confirmed."""
        quote_ok = self.quote_status.startswith("found") or self.quote_status == "no quote"
        return self.action.verified_on is None or not quote_ok


@functools.cache  # several milestones share one url; ask each server only once per run
def url_status(url: str | None) -> str:
    if not url:
        return "no url"
    try:
        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS, stream=True
        )
        response.close()
        return str(response.status_code)
    except requests.RequestException as error:
        return f"error: {type(error).__name__}"


def closest_wayback_snapshot(url: str | None, action: RegulatoryAction) -> str | None:
    """Ask the Wayback Machine for the archived copy closest to the action date."""
    if not url:
        return None
    params = {"url": url, "timestamp": action.date.strftime("%Y%m%d")}
    try:
        response = requests.get(
            WAYBACK_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        snapshot = response.json().get("archived_snapshots", {}).get("closest")
    except (requests.RequestException, ValueError):
        return None
    if snapshot and snapshot.get("available"):
        return snapshot["url"]
    return None


def check_sources(studies: list[Study]) -> list[SourceCheck]:
    checks = []
    for study in studies:
        for action in study.regulatory_actions:
            checks.append(
                SourceCheck(
                    study_id=study.study_id,
                    action=action,
                    url_status=url_status(action.url),
                    quote_status=quote_status(action.quote, [action.archive_url, action.url]),
                    wayback_url=None
                    if action.archive_url
                    else closest_wayback_snapshot(action.url, action),
                )
            )
    return checks
