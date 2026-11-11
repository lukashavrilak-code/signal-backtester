"""Evaluate 2x2 tables with the SQL in sql/04_metrics.sql and sql/05_signal_status.sql.

The statistics live in SQL. This module only loads the cells into DuckDB,
runs the two SQL files and returns the result rows as dictionaries.
"""

from dataclasses import dataclass

import duckdb

from backtester.config import Thresholds
from backtester.db import run_sql_file, set_thresholds


@dataclass
class TwoByTwo:
    a: int  # drug AND event
    b: int  # drug, no event
    c: int  # no drug, event
    d: int  # no drug, no event
    label: str = ""


def evaluate(
    con: duckdb.DuckDBPyConnection, tables: list[TwoByTwo], thresholds: Thresholds
) -> list[dict]:
    """Return one dict per table with the cells, PRR, ROR, CIs, chi-squared and signal flags."""
    con.execute(
        "CREATE OR REPLACE TABLE two_by_two "
        "(row_id INTEGER, label VARCHAR, a BIGINT, b BIGINT, c BIGINT, d BIGINT)"
    )
    con.executemany(
        "INSERT INTO two_by_two VALUES (?, ?, ?, ?, ?, ?)",
        [(i, t.label, t.a, t.b, t.c, t.d) for i, t in enumerate(tables)],
    )
    set_thresholds(con, thresholds)
    run_sql_file(con, "04_metrics.sql")
    run_sql_file(con, "05_signal_status.sql")

    result = con.execute("SELECT * FROM signal_status ORDER BY row_id")
    columns = [col[0] for col in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
