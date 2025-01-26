"""Tools for datetime related operations."""

import re
from datetime import datetime


def str_to_datetime(date_str: str) -> datetime:
    """
    Convert a string representing a date and time into a `datetime` object.

    The function uses regular expressions with named groups to extract components of a
    date and time (year, month, day, hour, minute, second). It supports formats like:
    - ISO 8601 (e.g., "2025-01-26T14:30:45")
    - Compact representations (e.g., "20250126143045")
    - Common variations (e.g., "2025/01/26 14:30")

    Parameters
    ----------
    date_str : str
        The input string containing the date and time.

    Returns
    -------
    datetime
        A `datetime` object representing the parsed date and time.

    Raises
    ------
    ValueError
        If the input string does not match the expected format or contains invalid date-time components.

    Examples
    --------
    >>> str_to_datetime("2025-01-26T14:30:45")
    datetime.datetime(2025, 1, 26, 14, 30, 45)
    >>> str_to_datetime("20250126143045")
    datetime.datetime(2025, 1, 26, 14, 30, 45)
    >>> str_to_datetime("2025/01/26 14:30")
    datetime.datetime(2025, 1, 26, 14, 30)
    >>> str_to_datetime("invalid-string")
    Traceback (most recent call last):
        ...
    ValueError: Input string 'invalid-string' does not match the expected date-time format.
    """
    pattern = re.compile(
        r"(?P<year>\d{4})[-/]?"
        r"(?P<month>\d{2})[-/]?"
        r"(?P<day>\d{2})[T ]?"
        r"(?P<hour>\d{2})?:?(?P<minute>\d{2})?:?(?P<second>\d{2})?"
    )
    match = pattern.search(date_str)

    if not match:
        raise ValueError(
            f"Input string '{date_str}' does not match the expected date-time format."
        )

    # Extract groups and convert them to integers, filling in defaults for missing values
    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour") or 0)
    minute = int(match.group("minute") or 0)
    second = int(match.group("second") or 0)

    try:
        return datetime(year, month, day, hour, minute, second)
    except ValueError as e:
        raise ValueError(
            f"Invalid date-time components extracted from '{date_str}': {e}"
        )
