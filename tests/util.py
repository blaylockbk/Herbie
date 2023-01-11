from datetime import datetime
from datetime import time
from datetime import timezone


def parse_datetime_time(value: str):
    return datetime.strptime(value, "%H:%M").time()


def is_time_between(start, end, x=None):
    """
    Return true if x is in the range [start, end].
    """

    # Default values.
    x = x or datetime.now().astimezone(timezone.utc)

    # Type conversions.
    if isinstance(x, datetime):
        x = x.time()
    if isinstance(start, int):
        start = time(hour=start)
    elif isinstance(start, str):
        start = parse_datetime_time(start)
    if isinstance(end, int):
        end = time(hour=end)
    elif isinstance(end, str):
        end = parse_datetime_time(end)

    # Sanity checks.
    if not isinstance(x, time):
        raise TypeError(f"Unknown type for 'x'. value={x}, type={type(x)}")
    if not isinstance(start, time):
        raise TypeError(f"Unknown type for 'start'. value={start}, type={type(start)}")
    if not isinstance(end, time):
        raise TypeError(f"Unknown type for 'end'. value={end}, type={type(end)}")

    # Comparison.
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
