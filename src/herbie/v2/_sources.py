"""
Source descriptors for Herbie v2.

Each descriptor tells the base class *how* to access data from a given
remote source: what URL to fetch, how to find the index, and how to
interpret it.  Model subclasses return a ``dict[str, Source]`` from their
``_build_sources()`` method; the base class consumes these without knowing
the specifics of each model.

Supported source types
----------------------
GribSource
    A GRIB2 file served over HTTP/HTTPS with a companion ``.idx`` or
    ``.index`` inventory file (the overwhelmingly common case for NOAA
    and ECMWF open-data).

EccodesGribSource
    Like GribSource but the index file uses the eccodes JSON-lines
    format rather than wgrib2 colon-separated format.  Used for ECMWF
    IFS/AIFS.

ZarrSource
    A Zarr store accessible via a URL (``s3://``, ``gs://``, ``https://``).
    No index file; the inventory is inferred from the Zarr metadata.

DirectorySource
    A web directory where *each file* holds a single GRIB message.
    Inventory is built by scraping the directory listing and parsing
    filenames with a regex.  Used for Canadian MSC models (HRDPS, RDPS,
    GDPS) and some Navy products.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal


# ---------------------------------------------------------------------------
# GRIB2 sources
# ---------------------------------------------------------------------------

@dataclass
class GribSource:
    """A remote GRIB2 file accessible via HTTP/HTTPS."""

    url: str
    """Full URL to the GRIB2 file."""

    index_suffixes: list[str] = field(
        default_factory=lambda: [".idx", ".grib2.idx"]
    )
    """Suffixes to try when looking for the companion index file.
    Each suffix is *appended* to ``url`` in order.  The first one that
    exists is used.
    """

    index_style: Literal["wgrib2", "eccodes"] = "wgrib2"
    """Format of the index file produced by ``wgrib2 -s`` or eccodes."""


@dataclass
class EccodesGribSource:
    """A remote GRIB2 file whose index was created with ecCodes (ECMWF)."""

    url: str
    index_suffixes: list[str] = field(default_factory=lambda: [".index"])
    index_style: Literal["wgrib2", "eccodes"] = "eccodes"


# ---------------------------------------------------------------------------
# Zarr source
# ---------------------------------------------------------------------------

@dataclass
class ZarrSource:
    """A cloud-native Zarr store."""

    url: str
    """Store URL, e.g. ``s3://noaa-hrrr-bdp-pds/hrrr.zarr`` or a GCS path."""

    consolidated: bool = True
    """Whether the Zarr store has a consolidated ``.zmetadata`` file."""

    open_kwargs: dict = field(default_factory=dict)
    """Extra keyword arguments forwarded to ``xarray.open_zarr``."""

    storage_options: dict = field(default_factory=dict)
    """``fsspec`` storage options (credentials, endpoint URL, etc.)."""


# ---------------------------------------------------------------------------
# Directory source  (one GRIB message per file — Canadian/Navy models)
# ---------------------------------------------------------------------------

@dataclass
class DirectorySource:
    """
    A web directory where each file contains one GRIB message.

    Inventory is built by scraping the HTML directory listing and parsing
    each filename with ``file_pattern``.  ``parse_metadata`` receives the
    matched filename and returns a dict of metadata that becomes one row
    in the inventory DataFrame.
    """

    url: str
    """URL of the directory listing (ends with ``/``)."""

    file_pattern: str
    """
    Regex applied to each filename in the directory listing.
    Named groups are captured as metadata columns.  Unmatched filenames
    are silently ignored.

    Example for HRDPS::

        r"(?P<date>\\d{8}T\\d{2}Z)_MSC_HRDPS_(?P<variable>\\w+)_"
        r"(?P<level>[\\w.-]+)_RLatLon(?P<res>[\\d.]+)_PT(?P<fxx>\\d+)H\\.grib2$"
    """

    parse_metadata: Callable[[str], dict] | None = None
    """
    Optional callable ``(filename: str) -> dict`` for richer parsing
    beyond what named regex groups provide (e.g. unit conversions,
    level standardisation).  If *None* the regex named groups alone are
    used.
    """

    index_style: Literal["directory"] = "directory"


# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

Source = GribSource | EccodesGribSource | ZarrSource | DirectorySource
