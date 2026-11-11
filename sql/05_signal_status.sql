-- 05_signal_status.sql
-- Signal criteria applied to the metrics table (output of 04_metrics.sql).
--
-- Thresholds come from config/settings.yaml and are set as DuckDB variables
-- by backtester.db.set_thresholds() before this file runs:
--   prr_min, chi2_min, n_min, ror_lower_min (DOUBLE), chi2_use_yates (BOOLEAN)
--
-- Evans criteria (Evans et al. 2001): PRR >= 2 AND chi-squared >= 4 AND a >= 3
-- ROR criterion (EudraVigilance practice): lower 95% CI of ROR > 1 AND a >= 3
-- Rows with NULL metrics (a zero cell) never count as a signal.

CREATE OR REPLACE TABLE signal_status AS
SELECT
    *,
    CASE WHEN getvariable('chi2_use_yates') THEN chi2_yates ELSE chi2_uncorrected END AS chi2,
    coalesce(
        prr >= getvariable('prr_min')
        AND (CASE WHEN getvariable('chi2_use_yates') THEN chi2_yates ELSE chi2_uncorrected END)
            >= getvariable('chi2_min')
        AND a >= getvariable('n_min'),
        false
    ) AS evans_signal,
    coalesce(
        ror_lo95 > getvariable('ror_lower_min')
        AND a >= getvariable('n_min'),
        false
    ) AS ror_signal
FROM metrics;
