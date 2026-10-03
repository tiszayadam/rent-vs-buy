"""Implied yearly growth and inflation from KSH yearly rent and house indices.

For each year-to-year step:

- real growth     = real[t] / real[t-1] - 1
- nominal growth  = nominal[t] / nominal[t-1] - 1
- implied inflation = (1 + nominal growth) / (1 + real growth) - 1

  which is the same as deflator[t] / deflator[t-1] - 1 with
  deflator = 100 * nominal / real.

The two files are compared on overlapping years. They need not match:
rent and Budapest house prices can diverge in real terms, and only implied
inflation should be close if both series use the same CPI deflator.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from ksh_yearly import HISTORICAL_DIR


def load_yearly(path: Path) -> list[tuple[int, float, float]]:
    rows: list[tuple[int, float, float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for line in reader:
            rows.append((int(line["year"]), float(line["nominal"]), float(line["real"])))
    if len(rows) < 2:
        raise ValueError(f"{path} needs at least two years")
    return rows


def yoy_rates(rows: list[tuple[int, float, float]]) -> list[dict[str, float | int]]:
    out: list[dict[str, float | int]] = []
    for (y0, nom0, real0), (y1, nom1, real1) in zip(rows, rows[1:]):
        if real0 == 0 or nom0 == 0:
            raise ValueError(f"zero index level in {y0}")
        g_real = real1 / real0 - 1.0
        g_nom = nom1 / nom0 - 1.0
        implied_inf = (1.0 + g_nom) / (1.0 + g_real) - 1.0
        out.append(
            {
                "from_year": y0,
                "to_year": y1,
                "real_pct": 100.0 * g_real,
                "nominal_pct": 100.0 * g_nom,
                "implied_inflation_pct": 100.0 * implied_inf,
            }
        )
    return out


def by_to_year(steps: list[dict[str, float | int]]) -> dict[int, dict[str, float | int]]:
    return {int(step["to_year"]): step for step in steps}


def rmse(values: list[float]) -> float:
    if not values:
        return float("nan")
    return math.sqrt(sum(v * v for v in values) / len(values))


def fmt(value: float) -> str:
    return f"{value:7.2f}"


def compare(
    rent_steps: list[dict[str, float | int]],
    house_steps: list[dict[str, float | int]],
) -> list[dict[str, float | int]]:
    rent_map = by_to_year(rent_steps)
    house_map = by_to_year(house_steps)
    years = sorted(set(rent_map) & set(house_map))
    rows: list[dict[str, float | int]] = []
    for year in years:
        r = rent_map[year]
        h = house_map[year]
        rows.append(
            {
                "from_year": r["from_year"],
                "to_year": year,
                "rent_real_pct": r["real_pct"],
                "house_real_pct": h["real_pct"],
                "real_diff_pct": float(h["real_pct"]) - float(r["real_pct"]),
                "rent_nominal_pct": r["nominal_pct"],
                "house_nominal_pct": h["nominal_pct"],
                "nominal_diff_pct": float(h["nominal_pct"]) - float(r["nominal_pct"]),
                "rent_implied_inflation_pct": r["implied_inflation_pct"],
                "house_implied_inflation_pct": h["implied_inflation_pct"],
                "inflation_diff_pct": float(h["implied_inflation_pct"])
                - float(r["implied_inflation_pct"]),
            }
        )
    return rows


def print_table(rows: list[dict[str, float | int]]) -> None:
    print(
        "  years  | rent real | house real | d real |"
        " rent nom | house nom | d nom |"
        " rent inf | house inf | d inf"
    )
    print("-" * 108)
    for row in rows:
        print(
            f"{int(row['from_year'])}-{int(row['to_year'])} |"
            f"{fmt(float(row['rent_real_pct']))} |"
            f"{fmt(float(row['house_real_pct']))} |"
            f"{fmt(float(row['real_diff_pct']))} |"
            f"{fmt(float(row['rent_nominal_pct']))} |"
            f"{fmt(float(row['house_nominal_pct']))} |"
            f"{fmt(float(row['nominal_diff_pct']))} |"
            f"{fmt(float(row['rent_implied_inflation_pct']))} |"
            f"{fmt(float(row['house_implied_inflation_pct']))} |"
            f"{fmt(float(row['inflation_diff_pct']))}"
        )


def print_summary(rows: list[dict[str, float | int]]) -> None:
    if not rows:
        print("no overlapping years")
        return
    keys = ("real_diff_pct", "nominal_diff_pct", "inflation_diff_pct")
    labels = ("real growth", "nominal growth", "implied inflation")
    print()
    print("house minus rent, overlapping years (percentage points)")
    for key, label in zip(keys, labels):
        diffs = [float(row[key]) for row in rows]
        mean = sum(diffs) / len(diffs)
        print(
            f"  {label:20}  RMSE {rmse(diffs):6.2f}  "
            f"mean {mean:6.2f}  max abs {max(abs(v) for v in diffs):6.2f}"
        )


def write_csv(rows: list[dict[str, float | int]], dest: Path) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with dest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rent",
        type=Path,
        default=HISTORICAL_DIR / "KSH_rent_index_yearly.csv",
    )
    parser.add_argument(
        "--house",
        type=Path,
        default=HISTORICAL_DIR / "KSH_home_price_index_yearly.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=HISTORICAL_DIR / "KSH_implied_yearly_rates.csv",
    )
    args = parser.parse_args()
    rent_steps = yoy_rates(load_yearly(args.rent))
    house_steps = yoy_rates(load_yearly(args.house))
    rows = compare(rent_steps, house_steps)
    print_table(rows)
    print_summary(rows)
    write_csv(rows, args.output)
    print(f"\nwrote {args.output}")


if __name__ == "__main__":
    main()
