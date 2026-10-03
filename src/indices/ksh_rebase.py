"""Rebase yearly KSH rent and house indices so 2026 equals 100.

Each series (nominal, real) is scaled independently:

    new_t = old_t / old_2026 * 100

Year-over-year growth rates are unchanged; only the index level is
rewritten so the latest observation is the base. Implied inflation from
(1 + g_nominal) / (1 + g_real) - 1 is therefore unchanged as well.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from indices.ksh_yearly import HISTORICAL_DIR
except ImportError:
    from ksh_yearly import HISTORICAL_DIR


def load_yearly(path: Path) -> list[tuple[int, float, float]]:
    rows: list[tuple[int, float, float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for line in reader:
            rows.append((int(line["year"]), float(line["nominal"]), float(line["real"])))
    if not rows:
        raise ValueError(f"{path} is empty")
    return rows


def rebase_to_year(
    rows: list[tuple[int, float, float]],
    base_year: int,
) -> list[tuple[int, float, float]]:
    bases = [row for row in rows if row[0] == base_year]
    if not bases:
        raise ValueError(f"no observation for base year {base_year}")
    _, nom_base, real_base = bases[0]
    if nom_base == 0 or real_base == 0:
        raise ValueError(f"zero index level in {base_year}")
    return [
        (year, 100.0 * nominal / nom_base, 100.0 * real / real_base)
        for year, nominal, real in rows
    ]


def write_yearly(path: Path, rows: list[tuple[int, float, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["year", "nominal", "real"])
        for year, nominal, real in rows:
            writer.writerow([year, f"{nominal:.4f}", f"{real:.4f}"])


def rebase_file(source: Path, dest: Path, base_year: int) -> Path:
    write_yearly(dest, rebase_to_year(load_yearly(source), base_year))
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-year", type=int, default=2026)
    args = parser.parse_args()
    jobs = (
        (
            HISTORICAL_DIR / "KSH_rent_index_yearly.csv",
            HISTORICAL_DIR / "KSH_rent_index_yearly_base2026.csv",
        ),
        (
            HISTORICAL_DIR / "KSH_home_price_index_yearly.csv",
            HISTORICAL_DIR / "KSH_home_price_index_yearly_base2026.csv",
        ),
    )
    for source, dest in jobs:
        rebase_file(source, dest, args.base_year)
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
