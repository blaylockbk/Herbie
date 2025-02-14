from herbie import Herbie
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Herbie CLI for accessing GRIB2 files."
    )
    parser.add_argument(
        "-d",
        "--date",
        required=True,
        help="Model initialization datetime in ISO format (e.g., 2024-01-01T01).",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="hrrr",
        help="Model name (e.g., hrrr).",
    )
    parser.add_argument(
        "-p",
        "--priority",
        nargs="+",
        default=["aws", "nomads"],
        help="Source priority list for data retrieval.",
    )
    parser.add_argument(
        "-f",
        "--fxx",
        type=int,
        default=0,
        help="Forecast lead time in hours.",
    )
    parser.add_argument(
        "-i",
        "--index",
        action="store_true",
        help="Return the index file instead of the GRIB file.",
    )

    args = parser.parse_args()

    # Create an instance of the Herbie class with the provided arguments
    H = Herbie(
        date=args.date,
        model=args.model,
        priority=args.priority,
        fxx=args.fxx,
        verbose=False,
    )

    # Return the value of the H.grb or H.idx object based on the index argument
    if args.index:
        print(H.idx)
    else:
        print(H.grib)


if __name__ == "__main__":
    main()
