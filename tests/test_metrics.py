"""PRR, ROR, confidence intervals and chi-squared against hand-calculated 2x2 tables.

Reference example (calculate it yourself in a spreadsheet):

                  event   no event
    drug (PS/SS)    a=10     b=90     (a+b = 100)
    other drugs     c=40     d=860    (c+d = 900)        N = 1000

    PRR = (10/100) / (40/900)                      = 2.25
    SE(ln PRR) = sqrt(1/10 - 1/100 + 1/40 - 1/900) = 0.33747
    PRR 95% CI = exp(ln 2.25 -/+ 1.96 * 0.33747)   = 1.1612 to 4.3596

    ROR = (10*860) / (90*40)                       = 2.3889
    SE(ln ROR) = sqrt(1/10 + 1/90 + 1/40 + 1/860)  = 0.37050
    ROR 95% CI = exp(ln 2.3889 -/+ 1.96 * 0.37050) = 1.1556 to 4.9383

    chi2 (Yates) = 1000 * (|8600 - 3600| - 500)^2 / (100 * 900 * 50 * 950) = 4.7368
    chi2 (no correction) = 1000 * (8600 - 3600)^2 / (100 * 900 * 50 * 950) = 5.8480
"""

import pytest

from backtester.metrics import TwoByTwo, evaluate


def test_reference_example(con, thresholds):
    row = evaluate(con, [TwoByTwo(a=10, b=90, c=40, d=860)], thresholds)[0]

    assert row["n_total"] == 1000
    assert row["prr"] == pytest.approx(2.25)
    assert row["prr_lo95"] == pytest.approx(1.1612, abs=1e-4)
    assert row["prr_hi95"] == pytest.approx(4.3596, abs=1e-4)
    assert row["ror"] == pytest.approx(2.3889, abs=1e-4)
    assert row["ror_lo95"] == pytest.approx(1.1556, abs=1e-4)
    assert row["ror_hi95"] == pytest.approx(4.9383, abs=1e-4)
    assert row["chi2_yates"] == pytest.approx(4.7368, abs=1e-4)
    assert row["chi2_uncorrected"] == pytest.approx(5.8480, abs=1e-4)


def test_prr_exactly_two_has_no_rounding_noise(con, thresholds):
    # (10/100) / (50/1000) = 2 exactly; the threshold test ">= 2" must not fail on 1.9999999
    row = evaluate(con, [TwoByTwo(a=10, b=90, c=50, d=950)], thresholds)[0]
    assert row["prr"] == 2.0


@pytest.mark.parametrize(
    "cells",
    [
        dict(a=0, b=100, c=40, d=860),  # no reports with drug AND event
        dict(a=10, b=0, c=40, d=860),  # every drug report has the event
        dict(a=10, b=90, c=0, d=900),  # the event never occurs with other drugs
    ],
)
def test_zero_cell_gives_null_metrics(con, thresholds, cells):
    row = evaluate(con, [TwoByTwo(**cells)], thresholds)[0]
    for column in ("prr", "prr_lo95", "ror", "ror_lo95", "chi2_yates", "chi2_uncorrected"):
        assert row[column] is None
    assert row["evans_signal"] is False
    assert row["ror_signal"] is False


def test_several_tables_keep_their_order_and_labels(con, thresholds):
    tables = [
        TwoByTwo(a=10, b=90, c=40, d=860, label="first"),
        TwoByTwo(a=1, b=99, c=10, d=890, label="second"),
    ]
    rows = evaluate(con, tables, thresholds)
    assert [r["label"] for r in rows] == ["first", "second"]
    assert rows[1]["prr"] == pytest.approx((1 / 100) / (10 / 900))
