"""Turn KSH index downloads into yearly CSVs (Q1 rent, January Budapest house prices)."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_DIR = REPO_ROOT / "indices_historical"

_Q1 = re.compile(r"^Q1\s+(\d{4})$")
_JANUARY = re.compile(r"^(\d{4})\.01\.?$")


def write_yearly_csv(rows: list[tuple[int, float, float]], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["year", "nominal", "real"])
        for year, nominal, real in rows:
            writer.writerow([year, nominal, real])


def q1_rent_rows(source: Path) -> list[tuple[int, float, float]]:
    rows: list[tuple[int, float, float]] = []
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            raise ValueError(f"{source} is empty")
        for line in reader:
            if len(line) < 3:
                continue
            match = _Q1.match(line[0].strip())
            if not match:
                continue
            year = int(match.group(1))
            rows.append((year, float(line[1]), float(line[2])))
    if not rows:
        raise ValueError(f"no Q1 rows in {source}")
    return rows


def january_budapest_house_rows(source: Path) -> list[tuple[int, float, float]]:
    """January of each year; Budapest nominal and real columns."""
    rows: list[tuple[int, float, float]] = []
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            raise ValueError(f"{source} is empty")
        for line in reader:
            if len(line) < 5:
                continue
            match = _JANUARY.match(line[0].strip().strip('"'))
            if not match:
                continue
            year = int(match.group(1))
            budapest_real = float(line[2])
            budapest_nominal = float(line[4])
            rows.append((year, budapest_nominal, budapest_real))
    if not rows:
        raise ValueError(f"no January Budapest rows in {source}")
    return rows


def convert_rent(
    source: Path | None = None,
    output: Path | None = None,
) -> Path:
    source = source or HISTORICAL_DIR / "KSH_rent_index.csv"
    output = output or HISTORICAL_DIR / "KSH_rent_index_yearly.csv"
    write_yearly_csv(q1_rent_rows(source), output)
    return output


def convert_house(
    source: Path | None = None,
    output: Path | None = None,
) -> Path:
    source = source or HISTORICAL_DIR / "KSH_home_price_index.csv"
    output = output or HISTORICAL_DIR / "KSH_home_price_index_yearly.csv"
    write_yearly_csv(january_budapest_house_rows(source), output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "series",
        nargs="*",
        choices=("rent", "house"),
        help="which series to convert (default: both)",
    )
    args = parser.parse_args()
    series = args.series or ["rent", "house"]
    if "rent" in series:
        dest = convert_rent()
        print(f"wrote rent years to {dest}")
    if "house" in series:
        dest = convert_house()
        print(f"wrote house years to {dest}")


if __name__ == "__main__":
    main()
