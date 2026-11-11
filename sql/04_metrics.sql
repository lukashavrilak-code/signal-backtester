-- 04_metrics.sql
-- Disproportionality metrics from a 2x2 contingency table.
--
-- Input table: two_by_two, one row per (study, drug, event, cutoff) with the cells
--   a = reports with the drug (suspect) AND the event
--   b = reports with the drug (suspect), WITHOUT the event
--   c = reports WITHOUT the drug (suspect), WITH the event
--   d = all other reports
-- Any extra columns (keys such as study_id or cutoff) are passed through unchanged.
--
-- Output table: metrics = two_by_two + PRR, ROR, 95% CIs and chi-squared.
-- If any cell is 0 the metrics are NULL ("insufficient data"). No +0.5 correction is applied.

CREATE OR REPLACE TABLE metrics AS
WITH cells AS (
    SELECT
        *,
        a::DOUBLE AS a_,
        b::DOUBLE AS b_,
        c::DOUBLE AS c_,
        d::DOUBLE AS d_,
        (a > 0 AND b > 0 AND c > 0 AND d > 0) AS has_all_cells
    FROM two_by_two
),
point_estimates AS (
    SELECT
        *,
        a_ + b_ + c_ + d_ AS n_total,
        -- PRR = [a / (a+b)] / [c / (c+d)], written as one division to avoid rounding noise
        CASE WHEN has_all_cells THEN (a_ * (c_ + d_)) / (c_ * (a_ + b_)) END AS prr,
        -- standard error of ln(PRR)
        CASE WHEN has_all_cells
             THEN sqrt(1 / a_ - 1 / (a_ + b_) + 1 / c_ - 1 / (c_ + d_)) END AS prr_se_log,
        -- ROR = (a*d) / (b*c)
        CASE WHEN has_all_cells THEN (a_ * d_) / (b_ * c_) END AS ror,
        -- standard error of ln(ROR)
        CASE WHEN has_all_cells
             THEN sqrt(1 / a_ + 1 / b_ + 1 / c_ + 1 / d_) END AS ror_se_log
    FROM cells
)
SELECT
    * EXCLUDE (a_, b_, c_, d_, has_all_cells, prr_se_log, ror_se_log),
    -- 95% confidence intervals are symmetric on the log scale: exp(ln(x) +/- 1.96 * SE)
    exp(ln(prr) - 1.96 * prr_se_log) AS prr_lo95,
    exp(ln(prr) + 1.96 * prr_se_log) AS prr_hi95,
    exp(ln(ror) - 1.96 * ror_se_log) AS ror_lo95,
    exp(ln(ror) + 1.96 * ror_se_log) AS ror_hi95,
    -- Pearson chi-squared with Yates continuity correction (1 degree of freedom)
    CASE WHEN has_all_cells THEN
        n_total * power(greatest(abs(a_ * d_ - b_ * c_) - n_total / 2, 0), 2)
        / ((a_ + b_) * (c_ + d_) * (a_ + c_) * (b_ + d_))
    END AS chi2_yates,
    -- Pearson chi-squared without correction (reported for comparison)
    CASE WHEN has_all_cells THEN
        n_total * power(a_ * d_ - b_ * c_, 2)
        / ((a_ + b_) * (c_ + d_) * (a_ + c_) * (b_ + d_))
    END AS chi2_uncorrected
FROM point_estimates;
