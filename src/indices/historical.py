"""Load realized KSH yearly indices (rebased so 2026 = 100) for display."""

from __future__ import annotations

from functools import lru_cache

from indices.ksh_rebase import load_yearly, rebase_to_year
from indices.ksh_yearly import (
    HISTORICAL_DIR,
    january_budapest_house_rows,
    q1_rent_rows,
)

LAST_HISTORY_YEAR = 2026
BASE_YEAR = 2026


def _split(
    rows: list[tuple[int, float, float]],
) -> tuple[list[int], list[float], list[float]]:
    years = [year for year, _, _ in rows]
    nominal = [nominal for _, nominal, _ in rows]
    real = [real for _, _, real in rows]
    return years, nominal, real


def _rows_for(yearly_name: str, raw_name: str, from_raw) -> list[tuple[int, float, float]]:
    yearly = HISTORICAL_DIR / yearly_name
    raw = HISTORICAL_DIR / raw_name
    if yearly.exists():
        rows = load_yearly(yearly)
    elif raw.exists():
        rows = from_raw(raw)
    else:
        raise FileNotFoundError(f"missing {yearly} and {raw}")
    return rebase_to_year(rows, BASE_YEAR)


@lru_cache(maxsize=1)
def rent_history() -> tuple[list[int], list[float], list[float]]:
    """years, nominal, real — Q1 rent, 2026 = 100."""
    return _split(
        _rows_for("KSH_rent_index_yearly.csv", "KSH_rent_index.csv", q1_rent_rows)
    )


@lru_cache(maxsize=1)
def house_history() -> tuple[list[int], list[float], list[float]]:
    """years, nominal, real — January Budapest house prices, 2026 = 100."""
    return _split(
        _rows_for(
            "KSH_home_price_index_yearly.csv",
            "KSH_home_price_index.csv",
            january_budapest_house_rows,
        )
    )


def implied_inflation_pct(
    years: list[int],
    nominal: list[float],
    real: list[float],
) -> tuple[list[int], list[float]]:
    """Inflation during year t that takes the index from t to t+1."""
    inf_years: list[int] = []
    inf_pct: list[float] = []
    for i in range(len(years) - 1):
        if real[i] == 0 or nominal[i] == 0:
            continue
        g_real = real[i + 1] / real[i] - 1.0
        g_nom = nominal[i + 1] / nominal[i] - 1.0
        inf_years.append(years[i])
        inf_pct.append(100.0 * ((1.0 + g_nom) / (1.0 + g_real) - 1.0))
    return inf_years, inf_pct
