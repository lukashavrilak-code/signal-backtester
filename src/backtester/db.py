"""DuckDB helpers: open a connection, pass thresholds to SQL, run the files in sql/."""

from pathlib import Path

import duckdb

from backtester.config import PROJECT_ROOT, Thresholds

SQL_DIR = PROJECT_ROOT / "sql"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "backtester.duckdb"


def connect(path: Path | str = ":memory:") -> duckdb.DuckDBPyConnection:
    """Open a DuckDB database. ':memory:' (the default) is used by tests and the 2x2 demo."""
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def set_thresholds(con: duckdb.DuckDBPyConnection, thresholds: Thresholds) -> None:
    """Expose the signal thresholds to SQL as variables, read there with getvariable('name')."""
    con.execute(f"SET VARIABLE prr_min = {float(thresholds.prr_min)}::DOUBLE")
    con.execute(f"SET VARIABLE chi2_min = {float(thresholds.chi2_min)}::DOUBLE")
    con.execute(f"SET VARIABLE n_min = {float(thresholds.n_min)}::DOUBLE")
    con.execute(f"SET VARIABLE ror_lower_min = {float(thresholds.ror_lower_min)}::DOUBLE")
    con.execute(f"SET VARIABLE chi2_use_yates = {bool(thresholds.chi2_use_yates)}")


def run_sql_file(con: duckdb.DuckDBPyConnection, name: str) -> None:
    """Run one file from sql/ (e.g. '04_metrics.sql')."""
    sql = (SQL_DIR / name).read_text(encoding="utf-8")
    con.execute(sql)
