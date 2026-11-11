# Signal Backtester

**Would a standard disproportionality method have flagged known drug safety signals before regulators acted, and by how many months?**

A portfolio project by [MY NAME] ([LinkedIn]([LINKEDIN URL]) · [CV]([CV URL])).
It backtests PRR/ROR signal detection on the FDA Adverse Event Reporting System (FAERS)
using only the reports that were available at each quarter-end.

> Research and education only. Not medical advice. Not a regulatory signal.

## Status

Work in progress. Milestone 1 (configuration, statistics and tests) is in place.

## Run locally

```bash
# 1. Install uv (https://docs.astral.sh/uv/) — or: python -m pip install --user uv
# 2. Install the pinned environment
uv sync
# 3. Run the tests
uv run pytest
# 4. Try the 2x2 calculator
uv run backtester demo-2x2
uv run backtester validate-config
```

The full README (live link, key result, diagram, limitations) is written in a later milestone.
