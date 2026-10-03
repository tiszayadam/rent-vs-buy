"""Expected yearly inflation and real price indices (not yet wired to the wealth model)."""

from __future__ import annotations

START_YEAR = 2027
N_YEARS = 30

DEFAULT_INFLATION_PCT = 3.0
DEFAULT_REAL_INDEX = 100.0


def years() -> list[int]:
    return list(range(START_YEAR, START_YEAR + N_YEARS))


def default_inflation_pct() -> list[float]:
    return [DEFAULT_INFLATION_PCT] * N_YEARS


def default_real_index() -> list[float]:
    return [DEFAULT_REAL_INDEX] * N_YEARS
