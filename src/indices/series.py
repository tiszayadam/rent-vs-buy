"""Expected yearly inflation and real/nominal price indices for the wealth model."""

from __future__ import annotations

START_YEAR = 2027
N_YEARS = 30
NEAR_TERM_EDITABLE_YEARS = 5
THEN_EVERY_N_YEARS = 5

DEFAULT_INFLATION_PCT = 3.0
DEFAULT_REAL_INDEX = 100.0
DEFAULT_EQUITY_RETURN_PCT = 8.0


def years() -> list[int]:
    return list(range(START_YEAR, START_YEAR + N_YEARS))


def editable_years(all_years: list[int] | None = None) -> list[int]:
    """Knots the user can move: the next five years, then every five years.

    The last year is always a knot so the tail can be interpolated rather than
    held flat. In-between years are filled by ``interpolate_from_knots``.
    """
    yrs = list(all_years) if all_years is not None else years()
    if not yrs:
        return []
    near = set(yrs[:NEAR_TERM_EDITABLE_YEARS])
    last_near = yrs[min(NEAR_TERM_EDITABLE_YEARS, len(yrs)) - 1]
    knots: list[int] = []
    for year in yrs:
        if year in near or (year - last_near) % THEN_EVERY_N_YEARS == 0:
            knots.append(year)
    if yrs[-1] not in knots:
        knots.append(yrs[-1])
    return knots


def interpolate_from_knots(
    values: list[float],
    all_years: list[int] | None = None,
    knot_years: list[int] | None = None,
) -> list[float]:
    """Linear interpolation between editable years; hold flat outside the knots."""
    yrs = list(all_years) if all_years is not None else years()
    if len(values) != len(yrs):
        raise ValueError("values must align with years")
    knots = list(knot_years) if knot_years is not None else editable_years(yrs)
    year_to_idx = {year: i for i, year in enumerate(yrs)}
    knot_idx = [year_to_idx[year] for year in knots if year in year_to_idx]
    out = [float(v) for v in values]
    if not knot_idx:
        return out
    first = knot_idx[0]
    for i in range(first):
        out[i] = out[first]
    for left, right in zip(knot_idx, knot_idx[1:]):
        span = right - left
        if span <= 0:
            continue
        start_val = out[left]
        end_val = out[right]
        for j in range(left + 1, right):
            t = (j - left) / span
            out[j] = start_val + (end_val - start_val) * t
    last = knot_idx[-1]
    for i in range(last + 1, len(out)):
        out[i] = out[last]
    return out


def default_inflation_pct() -> list[float]:
    return [DEFAULT_INFLATION_PCT] * N_YEARS


def default_real_index() -> list[float]:
    return [DEFAULT_REAL_INDEX] * N_YEARS


def default_equity_return_pct() -> list[float]:
    return [DEFAULT_EQUITY_RETURN_PCT] * N_YEARS


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


def index_at_year(index: list[float], year: int) -> float:
    """Yearly index, holding the last value if ``year`` runs past the series."""
    if not index:
        raise ValueError("index must not be empty")
    if year <= 0:
        return float(index[0])
    if year >= len(index):
        return float(index[-1])
    return float(index[year])


def real_huf(nominal: float, deflator: list[float], month: int) -> float:
    """Convert a nominal HUF stock to base-year (year-0) purchasing power.

    The yearly deflator is 100 in the first expected year; months in between
    use the same linear interpolation as the house index.
    """
    base = index_at_year(deflator, 0)
    if base == 0:
        raise ValueError("price deflator base must be non-zero")
    return nominal * base / index_at_month_linear(deflator, month)


def index_at_month_linear(index: list[float], month: int) -> float:
    """Linear interpolation between yearly index points. Month 0 is year 0."""
    if not index:
        raise ValueError("index must not be empty")
    if month <= 0:
        return float(index[0])
    t = month / 12.0
    left = int(t)
    if left >= len(index) - 1:
        return float(index[-1])
    frac = t - left
    a = float(index[left])
    b = float(index[left + 1])
    return a + (b - a) * frac


def rent_from_index(initial_monthly: float, nominal_rent_index: list[float], month: int) -> float:
    """Stepped rent: months 1–12 use year 0, then one index step per year."""
    if month <= 0:
        return 0.0
    base = index_at_year(nominal_rent_index, 0)
    if base == 0:
        raise ValueError("nominal rent index base must be non-zero")
    year = (month - 1) // 12
    return initial_monthly * index_at_year(nominal_rent_index, year) / base


def house_value_from_index(
    purchase_price: float,
    nominal_house_index: list[float],
    month: int,
    amortization_and_repairs_rate: float,
) -> float:
    """Market value follows the nominal house index; amort/repairs remain a value haircut."""
    base = index_at_year(nominal_house_index, 0)
    if base == 0:
        raise ValueError("nominal house index base must be non-zero")
    market = purchase_price * index_at_month_linear(nominal_house_index, month) / base
    return market * (1.0 - amortization_and_repairs_rate) ** (month / 12.0)
