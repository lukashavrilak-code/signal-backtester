"""Shared test fixtures.

Tests use their own fixed thresholds, so changing config/settings.yaml
never silently changes what the tests check.
"""

import pytest

from backtester.config import Thresholds
from backtester.db import connect


@pytest.fixture
def con():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture
def thresholds() -> Thresholds:
    return Thresholds(prr_min=2.0, chi2_min=4.0, chi2_use_yates=True, n_min=3, ror_lower_min=1.0)
