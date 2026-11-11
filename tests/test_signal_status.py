"""Signal criteria from sql/05_signal_status.sql.

Boundary tests insert ready-made metrics rows, so each threshold can be tested
with an exact value (e.g. chi-squared of exactly 4.0).
"""

import pytest

from backtester.config import Thresholds
from backtester.db import run_sql_file, set_thresholds
from backtester.metrics import TwoByTwo, evaluate


def status_for(con, thresholds, *, a, prr, chi2, ror_lo95):
    """Run only the signal-status SQL on one hand-made metrics row."""
    con.execute(
        "CREATE OR REPLACE TABLE metrics AS SELECT "
        "?::BIGINT AS a, ?::DOUBLE AS prr, ?::DOUBLE AS chi2_yates, "
        "?::DOUBLE AS chi2_uncorrected, ?::DOUBLE AS ror_lo95",
        [a, prr, chi2, chi2, ror_lo95],
    )
    set_thresholds(con, thresholds)
    run_sql_file(con, "05_signal_status.sql")
    return con.execute("SELECT evans_signal, ror_signal FROM signal_status").fetchone()


@pytest.mark.parametrize(
    ("a", "prr", "chi2", "expected_evans"),
    [
        (3, 2.0, 4.0, True),  # all three criteria exactly at the threshold -> signal
        (2, 5.0, 10.0, False),  # fewer than 3 reports
        (3, 1.99, 10.0, False),  # PRR just below 2
        (3, 5.0, 3.99, False),  # chi-squared just below 4
    ],
)
def test_evans_criteria_boundaries(con, thresholds, a, prr, chi2, expected_evans):
    evans, _ = status_for(con, thresholds, a=a, prr=prr, chi2=chi2, ror_lo95=0.5)
    assert evans is expected_evans


@pytest.mark.parametrize(
    ("a", "ror_lo95", "expected_ror"),
    [
        (3, 1.01, True),
        (3, 1.0, False),  # the lower bound must be strictly above 1
        (2, 3.0, False),  # fewer than 3 reports
    ],
)
def test_ror_criterion_boundaries(con, thresholds, a, ror_lo95, expected_ror):
    _, ror = status_for(con, thresholds, a=a, prr=1.0, chi2=0.0, ror_lo95=ror_lo95)
    assert ror is expected_ror


def test_yates_correction_can_change_the_decision(con, thresholds):
    # a=5, b=45, c=35, d=915: PRR 2.71, chi2 4.93 without correction but 3.43 with Yates
    table = TwoByTwo(a=5, b=45, c=35, d=915)

    with_yates = evaluate(con, [table], thresholds)[0]
    assert with_yates["chi2_uncorrected"] == pytest.approx(4.9342, abs=1e-4)
    assert with_yates["chi2_yates"] == pytest.approx(3.4265, abs=1e-4)
    assert with_yates["evans_signal"] is False

    no_yates = thresholds.model_copy(update={"chi2_use_yates": False})
    without_yates = evaluate(con, [table], no_yates)[0]
    assert without_yates["evans_signal"] is True


def test_thresholds_come_from_settings(con):
    strict = Thresholds(prr_min=3.0, chi2_min=4.0, chi2_use_yates=True, n_min=3, ror_lower_min=1.0)
    row = evaluate(con, [TwoByTwo(a=10, b=90, c=40, d=860)], strict)[0]
    assert row["evans_signal"] is False  # PRR 2.25 < 3
