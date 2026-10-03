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


def inflation_deflator(inflation_pct: list[float]) -> list[float]:
    """Cumulative price deflator, 100 in the first year (the base year).

    Later years compound every previous year's inflation rate:
    ``D[0] = 100``, ``D[t] = D[t-1] * (1 + inflation_pct[t-1] / 100)``.
    """
    if not inflation_pct:
        return []
    deflator = [100.0]
    for prev_pct in inflation_pct[:-1]:
        deflator.append(deflator[-1] * (1.0 + float(prev_pct) / 100.0))
    return deflator


def nominal_index(real_index: list[float], inflation_pct: list[float]) -> list[float]:
    """``nominal_t = real_t * deflator_t / 100`` with a shared base year."""
    deflator = inflation_deflator(inflation_pct)
    n = min(len(real_index), len(deflator))
    return [float(real_index[i]) * deflator[i] / 100.0 for i in range(n)]
