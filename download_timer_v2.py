#### /// script
#### requires-python = ">=3.13"
#### dependencies = [
####     "herbie-data>=2026.3.0",
#### ]
#### ///

"""
Herbie Download Timer Benchmark Tool.

This script benchmarks data retrieval performance across available Herbie
data sources (e.g., AWS, Azure, NOMADS, etc.) for a given forecast model
and search pattern.

Example usage:
    uv run download_timer.py
    uv run download_timer.py --model hrrr --search ":TMP:2 m:"
    uv run download_timer.py --verbose
"""

import argparse
import time
from datetime import date

from herbie.v2 import Herbie


# ---------------------------
# Bar rendering
# ---------------------------
def make_bar(t, t_min, t_max, max_width=30, min_width=1):
    if t_max == t_min:
        return "█" * max_width

    norm = (t - t_min) / (t_max - t_min)
    units = min_width + norm * (max_width - min_width)

    full_blocks = int(units)
    remainder = units - full_blocks
    half_block = 1 if remainder >= 0.5 else 0

    return "█" * full_blocks + ("▌" if half_block else "")


# ---------------------------
# Core run logic
# ---------------------------
def run(model, date, search, verbose=False):

    results = {}

    sources = Herbie.HRRR(date, verbose=False).SOURCES.keys()

    # ---------------------------
    # Download + timing
    # ---------------------------
    for source in sources:
        print(f"Downloading from {source:20s}", end="\r")
        try:
            H = Herbie.HRRR(
                date,
                priority=[source],
                overwrite=True,
                verbose=verbose,
            )

            start = time.time()
            f = H.download(search, overwrite=True)
            elapsed = time.time() - start

            # Not found case
            if H.grib is None:
                results[source] = ("not_found", None, None, None)
                continue

            # Field count
            nfields = len(H.inventory(search))

            # File size
            if isinstance(f, (list, tuple)):
                total_size = sum(fp.stat().st_size for fp in f)
            else:
                total_size = f.stat().st_size

            size_mb = total_size / (1024 * 1024)

            results[source] = ("ok", elapsed, nfields, size_mb)

        except Exception:
            results[source] = ("error", None, None, None)

    print(f"{' ':40s}", end="\r")

    # ---------------------------
    # Prepare valid items
    # ---------------------------
    valid_items = [
        (s, t, n, sz) for s, (status, t, n, sz) in results.items() if status == "ok"
    ]

    print("\nDownload Summary:")
    print(f"{model=}, {date=}, {search=}\n")

    # ---------------------------
    # Print successful downloads
    # ---------------------------
    if valid_items:
        t_min = min(t for _, t, _, _ in valid_items)
        t_max = max(t for _, t, _, _ in valid_items)

        valid_items.sort(key=lambda x: x[1])

        for source, t, nfields, size_mb in valid_items:
            bar = make_bar(t, t_min, t_max, max_width=30)
            print(
                f"{source:<10} {bar:<31} "
                f"{t:.3f} s  ({nfields} fields, {size_mb:.2f} MB)"
            )

    # ---------------------------
    # Print non-success cases
    # ---------------------------
    for source, (status, _, _, _) in results.items():
        if status == "not_found":
            print(f"{source:<10} NOT FOUND")
        elif status == "error":
            print(f"{source:<10} ERROR")


# ---------------------------
# CLI
# ---------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark GRIB download performance across Herbie data sources "
            "(AWS, Azure, NOMADS, etc.), including timing, file size, and field count."
        )
    )

    today = date.today()

    parser.add_argument("--model", default="hrrr", help="Model name (default: hrrr)")
    parser.add_argument("--date", default=today, help="Forecast date")
    parser.add_argument(
        "--search",
        default="TMP:",
        help="GRIB search string (e.g. ':TMP:', ':t:' for ifs model, ':GRD:')",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    return parser.parse_args()


def main():
    args = parse_args()

    run(
        model=args.model,
        date=args.date,
        search=args.search,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
