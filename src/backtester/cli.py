"""Command-line entry point: `uv run backtester <command>`.

Milestone 1 commands:
  demo-2x2         compute PRR, ROR, CIs and signal flags for one 2x2 table
  validate-config  load settings + all study files and print a summary
Later milestones add: download, load, qa, compute, screen, labels, export, site, serve, drafts, all.
"""

import argparse
import sys

from backtester.approvals import approval_status
from backtester.config import load_settings, load_studies
from backtester.db import connect
from backtester.metrics import TwoByTwo, evaluate
from backtester.sources import check_sources


def _fmt(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def cmd_demo_2x2(args: argparse.Namespace) -> None:
    settings = load_settings()
    table = TwoByTwo(a=args.a, b=args.b, c=args.c, d=args.d)
    row = evaluate(connect(), [table], settings.thresholds)[0]
    t = settings.thresholds

    print("                 event    no event")
    print(f"drug (suspect)  {table.a:>7}  {table.b:>10}")
    print(f"other drugs     {table.c:>7}  {table.d:>10}")
    print(f"N = {table.a + table.b + table.c + table.d}\n")
    print(f"PRR  {_fmt(row['prr'])}  (95% CI {_fmt(row['prr_lo95'])}-{_fmt(row['prr_hi95'])})")
    print(f"ROR  {_fmt(row['ror'])}  (95% CI {_fmt(row['ror_lo95'])}-{_fmt(row['ror_hi95'])})")
    print(
        f"chi2 {_fmt(row['chi2_yates'])} with Yates correction, "
        f"{_fmt(row['chi2_uncorrected'])} without"
    )
    print(
        f"\nEvans signal (PRR >= {t.prr_min}, chi2 >= {t.chi2_min}, n >= {t.n_min}): "
        f"{'YES' if row['evans_signal'] else 'no'}"
    )
    print(
        f"ROR signal (lower 95% CI > {t.ror_lower_min}, n >= {t.n_min}): "
        f"{'YES' if row['ror_signal'] else 'no'}"
    )


def cmd_validate_config(args: argparse.Namespace) -> None:
    settings = load_settings()
    studies = load_studies()
    print(f"settings.yaml OK (quarters {settings.quarters.start} to {settings.quarters.end})")
    print(f"{len(studies)} case studies:\n")
    for s in studies:
        action = s.primary_action
        unverified = [a for a in s.regulatory_actions if a.verified_on is None]
        print(f"- {s.study_id:<20} {s.title}")
        print(f"  primary action: {action.agency} {action.date} ({action.type})")
        print(
            f"  substances: {len(s.drug_group.substances)} | "
            f"event groups: {', '.join(s.event_groups)} | definitions: {s.definition_status} | "
            f"actions to verify: {len(unverified)}"
        )


def cmd_check_sources(args: argparse.Namespace) -> None:
    studies = load_studies()
    print("Regulatory milestones (quote = searched automatically in the source):\n")
    checks = check_sources(studies)
    for check in checks:
        a = check.action
        mark = "LOOK" if check.needs_attention else "ok  "
        verified = a.verified_on or "NOT VERIFIED"
        print(f"{mark} {check.study_id} | {a.agency} {a.date} | {a.type} | verified: {verified}")
        print(f"     quote: {check.quote_status} | url status: {check.url_status}")
        if check.needs_attention:
            print(f"     open: {a.archive_url or a.url or '-'}")
            if a.quote:
                print(f'     search for: "{a.quote}"')
            if check.wayback_url:
                print(f"     suggested archive_url: {check.wayback_url}")

    print("\nFirst US approval dates (compared with Drugs@FDA):\n")
    mismatches = 0
    for study in studies:
        for substance, date in study.drug_group.approval_dates.items():
            status = approval_status(substance, date)
            mismatches += status != "OK"
            print(f"{'ok  ' if status == 'OK' else 'LOOK'} {substance:<15} {date}  {status}")

    to_look = sum(check.needs_attention for check in checks) + mismatches
    print(f"\n{to_look} item(s) marked LOOK need a manual check; everything else was confirmed.")


def main() -> None:
    # Windows consoles default to a legacy code page; study titles contain an en dash.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="backtester", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo-2x2", help="evaluate one 2x2 table")
    demo.add_argument("--a", type=int, default=10, help="drug AND event")
    demo.add_argument("--b", type=int, default=90, help="drug, no event")
    demo.add_argument("--c", type=int, default=40, help="no drug, event")
    demo.add_argument("--d", type=int, default=860, help="no drug, no event")
    demo.set_defaults(func=cmd_demo_2x2)

    validate = sub.add_parser("validate-config", help="check settings and study files")
    validate.set_defaults(func=cmd_validate_config)

    sources = sub.add_parser(
        "check-sources", help="check links, quotes and approval dates against their sources"
    )
    sources.set_defaults(func=cmd_check_sources)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
