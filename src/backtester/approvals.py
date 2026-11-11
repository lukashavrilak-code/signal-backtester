"""Compare the approval_dates in the study files with Drugs@FDA (openFDA `drug/drugsfda`).

Rule: the first US approval of a substance is the earliest approval of an original
application (submission type ORIG, status AP) among the NDAs that contain it.
Drugs@FDA is an official, machine-readable FDA database, so these dates are
checked by this script instead of by hand. The YAML stays the source of truth;
the check only reports differences.
"""

import datetime as dt
import os

import requests

DRUGSFDA_URL = "https://api.fda.gov/drug/drugsfda.json"
USER_AGENT = "signal-backtester/0.1 (approval date checker)"
TIMEOUT_SECONDS = 30


def first_nda_approval(substance: str) -> dt.date | None:
    """Earliest approved original NDA that contains the substance, or None if not found."""
    params = {
        "search": f'products.active_ingredients.name:"{substance}" AND application_number:NDA*',
        "limit": 100,
    }
    api_key = os.environ.get("OPENFDA_API_KEY")
    if api_key:
        params["api_key"] = api_key
    response = requests.get(
        DRUGSFDA_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS
    )
    if response.status_code == 404:  # openFDA answers 404 when nothing matches
        return None
    response.raise_for_status()

    dates = [
        submission["submission_status_date"]
        for application in response.json()["results"]
        for submission in application.get("submissions", [])
        if submission.get("submission_type") == "ORIG"
        and submission.get("submission_status") == "AP"
    ]
    if not dates:
        return None
    return dt.datetime.strptime(min(dates), "%Y%m%d").date()


def approval_status(substance: str, yaml_date: dt.date) -> str:
    """'OK', 'MISMATCH (Drugs@FDA: <date>)', 'not in Drugs@FDA' or 'error: ...'."""
    try:
        fda_date = first_nda_approval(substance)
    except requests.RequestException as error:
        return f"error: {type(error).__name__}"
    if fda_date is None:
        return "not in Drugs@FDA"
    return "OK" if fda_date == yaml_date else f"MISMATCH (Drugs@FDA: {fda_date})"
