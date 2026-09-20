"""GFS, GDAS, and GFSwave model templates for Herbie v2."""

from __future__ import annotations

from typing import ClassVar

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource, ZarrCatalogEntry


# ---------------------------------------------------------------------------
# GFS  –  Main Deterministic Forecast
# ---------------------------------------------------------------------------


class GFS(HerbieModel):
    """
    Global Forecast System (GFS) — NCEP global deterministic NWP model.

    NOAA's primary operational global model, produced four times per day
    (00, 06, 12, 18 UTC) on a global lat-lon grid with forecasts to 384 h.
    Data are available on three resolutions and in two parameter subsets
    (``pgrb2`` / ``pgrb2b``), a combined file (``pgrb2full``), and a
    surface-flux product on the native Gaussian grid (``sfluxgrb``).

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).  Must be on a 6-hourly boundary.
    step : int, default 0
        Forecast lead time in hours.  Valid range: 0–384.

        * For ``pgrb2.0p25`` / ``pgrb2b.0p25``: hourly f001–f120, then
          3-hourly f123–f384.
        * For all 0.50° and 1.00° products: f000 for analysis, then
          3-hourly f003, f006, … only (f001 and f002 are **not** produced).
        * For ``sfluxgrb``: hourly f001–f384 (no f000 file).
        * For ``pgrb2full.0p50``: f000 then 3-hourly f003–f384.

    product : str, default ``'pgrb2.0p25'``
        GRIB2 product/resolution combination.  See table below.

    Product table
    -------------
    *pgrb2* family (most commonly used parameters):

    +------------------+-----------------------------------------------------+
    | ``pgrb2.0p25``   | Common fields, global 0.25 deg lat-lon (default)    |
    | ``pgrb2.0p50``   | Common fields, global 0.50 deg lat-lon              |
    | ``pgrb2.1p00``   | Common fields, global 1.00 deg lat-lon              |
    +------------------+-----------------------------------------------------+

    *pgrb2b* family (supplementary / least commonly used parameters):

    +------------------+-----------------------------------------------------+
    | ``pgrb2b.0p25``  | Supplementary fields, 0.25 deg lat-lon              |
    | ``pgrb2b.0p50``  | Supplementary fields, 0.50 deg lat-lon              |
    | ``pgrb2b.1p00``  | Supplementary fields, 1.00 deg lat-lon              |
    +------------------+-----------------------------------------------------+

    *pgrb2full* (concatenation of pgrb2 + pgrb2b at 0.50 deg):

    +-------------------+----------------------------------------------------+
    | ``pgrb2full.0p50``| All fields combined, 0.50 deg lat-lon              |
    +-------------------+----------------------------------------------------+

    *sfluxgrb* (surface flux on the native T1534 semi-Lagrangian grid):

    +----------------+--------------------------------------------------------+
    | ``sfluxgrb``   | Surface flux fields; native Gaussian grid, f001-f384  |
    +----------------+--------------------------------------------------------+

    Handy aliases for ``product``:

    +------------------+-------------------+
    | ``'quarter'``    | ``pgrb2.0p25``    |
    | ``'half'``       | ``pgrb2.0p50``    |
    | ``'one'``        | ``pgrb2.1p00``    |
    | ``'0p25'``       | ``pgrb2.0p25``    |
    | ``'0p50'``       | ``pgrb2.0p50``    |
    | ``'1p00'``       | ``pgrb2.1p00``    |
    | ``'b0p25'``      | ``pgrb2b.0p25``   |
    | ``'b0p50'``      | ``pgrb2b.0p50``   |
    | ``'b1p00'``      | ``pgrb2b.1p00``   |
    | ``'full'``       | ``pgrb2full.0p50``|
    | ``'sflux'``      | ``sfluxgrb``      |
    +------------------+-------------------+

    Sources
    -------
    +-----------+--------------------------------------------------------------+
    | aws       | NOAA Big Data Program S3 (noaa-gfs-bdp-pds) -- recommended  |
    | nomads    | NCEP NOMADS HTTPS -- authoritative, ~2 days retention        |
    | ftpprd    | NCEP FTPPRD -- same data as NOMADS, alternate host           |
    | google    | Google Public Data (global-forecast-system GCS bucket)       |
    | azure     | Azure Open Datasets (noaagfs blob container)                 |
    | ncar_rda  | NCAR Research Data Archive ds084.1 -- 0.25 deg pgrb2 only,   |
    |           | long archive back to 2015; different filename convention     |
    +-----------+--------------------------------------------------------------+

    Notes
    -----
    * ``aws`` is recommended: no rate limits, global CDN, wide history.
    * ``nomads`` and ``ftpprd`` only keep ~48 hours of data.
    * ``ncar_rda`` uses a flat-directory layout with a different filename
      convention: ``gfs.0p25.YYYYMMDDHH.fFFF.grib2``.  Only 0.25 deg pgrb2.
    * ``sfluxgrb`` and ``pgrb2full.0p50`` are not mirrored on google/azure.

    References
    ----------
    NCO Products Inventory:
        https://www.nco.ncep.noaa.gov/pmb/products/gfs/
    GFS Overview (EMC):
        https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs.php
    AWS Open Data Registry:
        https://registry.opendata.aws/noaa-gfs-bdp-pds/

    Examples
    --------
    >>> from herbie.v2 import GFS
    >>> H = GFS("2024-01-15 00:00", step=0)                          # 0.25 deg analysis
    >>> H = GFS("2024-01-15 12:00", step=48, product="0p50")         # 0.50 deg forecast
    >>> H = GFS("2024-01-15 00:00", step=24, product="pgrb2b.0p25")  # supplementary
    >>> H = GFS("2024-01-15 00:00", step=6,  product="sflux")        # surface flux
    >>> H.status()
    >>> H.find().inventory("TMP:2 m above ground")
    """

    MODEL_NAME = "GFS"
    MODEL_DESCRIPTION = "Global Forecast System -- NCEP deterministic global NWP"
    MODEL_WEBSITES = {
        "NCO Products": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/",
        "EMC Overview": "https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs.php",
        "AWS Open Data": "https://registry.opendata.aws/noaa-gfs-bdp-pds/",
        "NOMADS": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/",
    }

    PARAMS = {
        "product": {
            "default": "pgrb2.0p25",
            "valid": [
                "pgrb2.0p25",
                "pgrb2.0p50",
                "pgrb2.1p00",
                "pgrb2b.0p25",
                "pgrb2b.0p50",
                "pgrb2b.1p00",
                "pgrb2full.0p50",
                "sfluxgrb",
            ],
            "aliases": {
                # resolution shorthands -> pgrb2 (most common subset)
                "0p25": "pgrb2.0p25",
                "0p50": "pgrb2.0p50",
                "1p00": "pgrb2.1p00",
                # friendly resolution names
                "quarter": "pgrb2.0p25",
                "half": "pgrb2.0p50",
                "one": "pgrb2.1p00",
                # pgrb2b shorthands
                "b0p25": "pgrb2b.0p25",
                "b0p50": "pgrb2b.0p50",
                "b1p00": "pgrb2b.1p00",
                # combined and flux shorthands
                "full": "pgrb2full.0p50",
                "sflux": "sfluxgrb",
            },
            "descriptions": {
                "pgrb2.0p25": (
                    "Most common fields, 0.25 deg global lat-lon; "
                    "hourly f001-f120, 3-hourly f123-f384"
                ),
                "pgrb2.0p50": (
                    "Most common fields, 0.50 deg global lat-lon; "
                    "f000 analysis, then 3-hourly f003-f384"
                ),
                "pgrb2.1p00": (
                    "Most common fields, 1.00 deg global lat-lon; "
                    "f000 analysis, then 3-hourly f003-f384"
                ),
                "pgrb2b.0p25": (
                    "Supplementary/less common fields, 0.25 deg; "
                    "same time steps as pgrb2.0p25"
                ),
                "pgrb2b.0p50": (
                    "Supplementary/less common fields, 0.50 deg; "
                    "f000 analysis, then 3-hourly f003-f384"
                ),
                "pgrb2b.1p00": (
                    "Supplementary/less common fields, 1.00 deg; "
                    "f000 analysis, then 3-hourly f003-f384"
                ),
                "pgrb2full.0p50": (
                    "All fields (pgrb2 + pgrb2b combined), 0.50 deg; "
                    "f000 analysis, then 3-hourly f003-f384; aws/nomads/ftpprd only"
                ),
                "sfluxgrb": (
                    "Surface flux fields on native T1534 semi-Lagrangian Gaussian grid; "
                    "hourly f001-f384 (no f000); aws/nomads/ftpprd only"
                ),
            },
        },
    }

    # ------------------------------------------------------------------
    # Zarr sources (cloud-optimised, no GRIB2 byte-range needed)
    # ------------------------------------------------------------------

    ZARR_SOURCES: ClassVar[dict] = {
        # ── dynamical.org analysis ─────────────────────────────────────────
        # Concatenation of the first 6 hours of every GFS forecast run,
        # providing a continuous hourly best-estimate analysis.
        # Dims: time × latitude × longitude
        # Time coverage: 2021-05-01 UTC to present, 1-hour steps.
        # Spatial: 0.25 deg global, longitude in [-180, 179.75].
        # License: CC BY 4.0
        # Citation: NOAA NWS NCEP GFS data processed by dynamical.org
        #   DOI: https://doi.org/10.5281/zenodo.18777399
        #
        # Variables (GRIB2 shortName in parentheses):
        #   temperature_2m (2t), minimum_temperature_2m (tmin),
        #   maximum_temperature_2m (tmax), relative_humidity_2m (2r),
        #   wind_u_10m (10u), wind_v_10m (10v),
        #   wind_u_100m (100u), wind_v_100m (100v),
        #   pressure_reduced_to_mean_sea_level (prmsl), pressure_surface (sp),
        #   precipitable_water_atmosphere (pwat), precipitation_surface (prate),
        #   percent_frozen_precipitation_surface (cpofp),
        #   categorical_rain_surface (crain), categorical_snow_surface (csnow),
        #   categorical_freezing_rain_surface (cfrzr),
        #   categorical_ice_pellets_surface (cicep),
        #   downward_short_wave_radiation_flux_surface (sdswrf),
        #   downward_long_wave_radiation_flux_surface (sdlwrf),
        #   total_cloud_cover_atmosphere (tcc),
        #   geopotential_height_cloud_ceiling (gh)
        ("dynamical", "analysis"): ZarrCatalogEntry(
            url="https://data.dynamical.org/noaa/gfs/analysis/latest.zarr",
            description=(
                "dynamical.org GFS analysis | 2021-05-01 to present | "
                "1-hr steps | 0.25 deg global | dims: time x latitude x longitude | "
                "21 surface variables | CC BY 4.0"
            ),
            time_dim="time",
            lead_time_dim=None,
            open_kwargs={"chunks": "auto"},
        ),
        # ── dynamical.org forecast ─────────────────────────────────────────
        # Archive of complete GFS forecast runs from 2021-05-01 to present.
        # Dims: init_time × lead_time × latitude × longitude
        # init_time: every 6 h (00/06/12/18 UTC), 2021-05-01 to present.
        # lead_time: 0-120 h hourly, 123-384 h 3-hourly (matches pgrb2.0p25).
        # Spatial: 0.25 deg global, longitude in [-180, 179.75].
        # License: CC BY 4.0
        # NOTE: Icechunk v2 migration in progress; URL may change slightly.
        #   Subscribe to dynamical.org updates for breaking change notice.
        #
        # Same 21 atmospheric variables as the analysis store, plus:
        #   expected_forecast_length, ingested_forecast_length, valid_time
        ("dynamical", "forecast"): ZarrCatalogEntry(
            url="https://data.dynamical.org/noaa/gfs/forecast/latest.zarr",
            description=(
                "dynamical.org GFS forecast | inits 2021-05-01 to present | "
                "6-hr init cadence | 0-384 hr lead time | 0.25 deg global | "
                "dims: init_time x lead_time x latitude x longitude | "
                "21 surface variables | CC BY 4.0"
            ),
            time_dim="init_time",
            lead_time_dim="lead_time",
            open_kwargs={"chunks": "auto"},
        ),
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]

        # All GFS atmospheric output lives under gfs.YYYYMMDD/HH/atmos/
        def _atmos(host):
            return f"{host}/gfs.{d:%Y%m%d}/{d:%H}/atmos"

        aws = _atmos("https://noaa-gfs-bdp-pds.s3.amazonaws.com")
        nomads = _atmos("https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod")
        ftpprd = _atmos("https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod")
        google = _atmos("https://storage.googleapis.com/global-forecast-system")
        azure = _atmos("https://noaagfs.blob.core.windows.net/gfs")

        idx = [".idx"]

        if product == "sfluxgrb":
            # Surface flux: distinct stem, no .idx files, 3 sources only
            stem = f"gfs.t{d:%H}z.sfluxgrbf{step:03d}.grib2"
            return {
                "aws": GribSource(f"{aws}/{stem}", []),
                "nomads": GribSource(f"{nomads}/{stem}", []),
                "ftpprd": GribSource(f"{ftpprd}/{stem}", []),
            }

        if product == "pgrb2full.0p50":
            # Combined file: aws/nomads/ftpprd only (not on google/azure)
            stem = f"gfs.t{d:%H}z.pgrb2full.0p50.f{step:03d}"
            return {
                "aws": GribSource(f"{aws}/{stem}", idx),
                "nomads": GribSource(f"{nomads}/{stem}", idx),
                "ftpprd": GribSource(f"{ftpprd}/{stem}", idx),
            }

        # All pgrb2.Rres and pgrb2b.Rres products share the same stem pattern
        stem = f"gfs.t{d:%H}z.{product}.f{step:03d}"

        sources = {
            "aws": GribSource(f"{aws}/{stem}", idx),
            "nomads": GribSource(f"{nomads}/{stem}", idx),
            "ftpprd": GribSource(f"{ftpprd}/{stem}", idx),
            "google": GribSource(f"{google}/{stem}", idx),
            "azure": GribSource(f"{azure}/{stem}", idx),
        }

        # NCAR RDA (ds084.1) -- 0.25 deg pgrb2 only; flat directory, different naming
        if product == "pgrb2.0p25":
            ncar_base = f"https://data.rda.ucar.edu/d084001/{d:%Y}/{d:%Y%m%d}"
            ncar_stem = f"gfs.0p25.{d:%Y%m%d%H}.f{step:03d}.grib2"
            sources["ncar_rda"] = GribSource(f"{ncar_base}/{ncar_stem}", idx)

        return sources


# ---------------------------------------------------------------------------
# GDAS  –  Global Data Assimilation System
# ---------------------------------------------------------------------------


class GDAS(HerbieModel):
    """
    Global Data Assimilation System (GDAS) — NCEP analysis and short-range.

    GDAS produces analyses and very short-range (0-9 h) forecasts four times
    per day.  It is the observation-assimilation backbone that initialises
    each GFS cycle.  Data are stored in the same AWS/GCS/Azure buckets as GFS
    but under a ``gdas.YYYYMMDD/HH/atmos/`` prefix.

    Parameters
    ----------
    date : str or datetime
        Analysis time (UTC).  Must be on a 6-hourly boundary.
    step : int, default 0
        Forecast lead time in hours.  Valid range: 0-9.
    product : str, default ``'pgrb2.0p25'``
        GRIB2 product.  See table below.

    Products
    --------
    +------------------+------------------------------------------------------+
    | ``pgrb2.0p25``   | Pressure-level fields, global 0.25 deg lat-lon       |
    | ``pgrb2.1p00``   | Pressure-level fields, global 1.00 deg lat-lon       |
    | ``sfluxgrb``     | Surface flux, T574 Gaussian grid, f000-f009          |
    +------------------+------------------------------------------------------+

    Aliases: ``'0p25'`` -> ``pgrb2.0p25``, ``'1p00'`` -> ``pgrb2.1p00``,
    ``'sflux'`` -> ``sfluxgrb``.

    Sources: aws, nomads, ftpprd, google, azure

    References
    ----------
    NCO Products Inventory:
        https://www.nco.ncep.noaa.gov/pmb/products/gfs/

    Examples
    --------
    >>> from herbie.v2 import GDAS
    >>> H = GDAS("2024-01-15 06:00", step=0)
    >>> H.find().inventory("TMP:500 mb")
    """

    MODEL_NAME = "GDAS"
    MODEL_DESCRIPTION = "Global Data Assimilation System -- NCEP analysis"
    MODEL_WEBSITES = {
        "NCO Products": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/",
        "NOMADS": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/",
    }

    PARAMS = {
        "product": {
            "default": "pgrb2.0p25",
            "valid": ["pgrb2.0p25", "pgrb2.1p00", "sfluxgrb"],
            "aliases": {
                "0p25": "pgrb2.0p25",
                "1p00": "pgrb2.1p00",
                "sflux": "sfluxgrb",
            },
            "descriptions": {
                "pgrb2.0p25": (
                    "Pressure-level analysis/short forecast, global 0.25 deg lat-lon"
                ),
                "pgrb2.1p00": (
                    "Pressure-level analysis/short forecast, global 1.00 deg lat-lon"
                ),
                "sfluxgrb": "Surface flux fields on T574 Gaussian grid; f000-f009",
            },
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]

        # GDAS lives in the same buckets as GFS but under gdas.YYYYMMDD/ prefix
        def _atmos(host):
            return f"{host}/gdas.{d:%Y%m%d}/{d:%H}/atmos"

        aws = _atmos("https://noaa-gfs-bdp-pds.s3.amazonaws.com")
        nomads = _atmos("https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod")
        ftpprd = _atmos("https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod")
        google = _atmos("https://storage.googleapis.com/global-forecast-system")
        azure = _atmos("https://noaagfs.blob.core.windows.net/gfs")

        idx = [".idx"]

        if product == "sfluxgrb":
            stem = f"gdas.t{d:%H}z.sfluxgrbf{step:03d}.grib2"
            return {
                "aws": GribSource(f"{aws}/{stem}", []),
                "nomads": GribSource(f"{nomads}/{stem}", []),
                "ftpprd": GribSource(f"{ftpprd}/{stem}", []),
            }

        # pgrb2.0p25 and pgrb2.1p00
        stem = f"gdas.t{d:%H}z.{product}.f{step:03d}"
        return {
            "aws": GribSource(f"{aws}/{stem}", idx),
            "nomads": GribSource(f"{nomads}/{stem}", idx),
            "ftpprd": GribSource(f"{ftpprd}/{stem}", idx),
            "google": GribSource(f"{google}/{stem}", idx),
            "azure": GribSource(f"{azure}/{stem}", idx),
        }


# ---------------------------------------------------------------------------
# GFS_Wave  –  GFS-coupled wave model (GFSwave)
# ---------------------------------------------------------------------------


class GFSWave(HerbieModel):
    """
    GFS-coupled wave model (GFSwave) -- replaced Multi-Grid WW3 on 2022-03-22.

    Provides significant wave height, period, direction, and related fields
    on several regional and global domains.  All domains cover f000-f384.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).  Must be on a 6-hourly boundary.
    step : int, default 0
        Forecast lead time in hours.  Valid range: 0-384.
    product : str, default ``'global.0p16'``
        Domain and resolution.  See table below.

    Products
    --------
    +-----------------+-------------------------------------------------------+
    | ``global.0p16`` | Global domain, 0.16 deg lat-lon (default)             |
    | ``global.0p25`` | Global domain, 0.25 deg lat-lon                       |
    | ``gsouth.0p25`` | Global South domain, 0.25 deg lat-lon                 |
    | ``arctic.9km``  | Arctic domain, ~9 km polar stereographic              |
    | ``epacif.0p16`` | East Pacific domain, 0.16 deg lat-lon                 |
    | ``wcoast.0p16`` | US West Coast domain, 0.16 deg lat-lon                |
    | ``atlocn.0p16`` | North Atlantic domain, 0.16 deg lat-lon               |
    +-----------------+-------------------------------------------------------+

    Aliases: ``'global'`` -> ``global.0p16``, ``'arctic'`` -> ``arctic.9km``,
    ``'epacif'`` -> ``epacif.0p16``, ``'wcoast'`` -> ``wcoast.0p16``,
    ``'atlocn'`` -> ``atlocn.0p16``.

    Notes
    -----
    * Files live under ``gfs.YYYYMMDD/HH/wave/gridded/`` on all archives.
    * The ``global.0p16`` product uses a short stem without a domain segment:
      ``gfswave.tCCz.fFFF.grib2``.  All other products include the domain
      identifier: ``gfswave.tCCz.<domain>.fFFF.grib2``.

    References
    ----------
    NCO Products Inventory (Wave section):
        https://www.nco.ncep.noaa.gov/pmb/products/gfs/

    Examples
    --------
    >>> from herbie.v2 import GFS_Wave
    >>> H = GFS_Wave("2024-01-15 00:00", step=24, product="atlocn.0p16")
    >>> H.find().inventory("HTSGW")
    >>> H = GFS_Wave("2024-01-15 00:00", step=0, product="arctic")
    """

    MODEL_NAME = "GFS_Wave"
    MODEL_DESCRIPTION = "GFS-coupled wave model (GFSwave)"
    MODEL_WEBSITES = {
        "NCO Products": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/",
        "AWS Open Data": "https://registry.opendata.aws/noaa-gfs-bdp-pds/",
    }

    PARAMS = {
        "product": {
            "default": "global.0p16",
            "valid": [
                "global.0p16",
                "global.0p25",
                "gsouth.0p25",
                "arctic.9km",
                "epacif.0p16",
                "wcoast.0p16",
                "atlocn.0p16",
            ],
            "aliases": {
                "global": "global.0p16",
                "arctic": "arctic.9km",
                "epacif": "epacif.0p16",
                "wcoast": "wcoast.0p16",
                "atlocn": "atlocn.0p16",
            },
            "descriptions": {
                "global.0p16": (
                    "Global domain, 0.16 deg lat-lon; "
                    "short stem: gfswave.tCCz.fFFF.grib2 (no domain segment)"
                ),
                "global.0p25": "Global domain, 0.25 deg lat-lon",
                "gsouth.0p25": "Global South domain, 0.25 deg lat-lon",
                "arctic.9km": "Arctic domain, ~9 km polar stereographic grid",
                "epacif.0p16": "East Pacific domain, 0.16 deg lat-lon",
                "wcoast.0p16": "US West Coast domain, 0.16 deg lat-lon",
                "atlocn.0p16": "North Atlantic domain, 0.16 deg lat-lon",
            },
        },
    }

    # Product key -> WCOSS/S3 filename domain segment inserted into the stem.
    # None = global.0p16 special case (no domain segment in filename).
    _DOMAIN_STEM = {
        "global.0p16": None,
        "global.0p25": "0p25",
        "gsouth.0p25": "gsouth.0p25",
        "arctic.9km": "arctic9km",
        "epacif.0p16": "epacif.0p16",
        "wcoast.0p16": "wcoast.0p16",
        "atlocn.0p16": "atlocn.0p16",
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]

        domain_seg = self._DOMAIN_STEM[product]
        if domain_seg is None:
            # global.0p16: short stem, no domain segment
            stem = f"gfswave.t{d:%H}z.f{step:03d}.grib2"
        else:
            stem = f"gfswave.t{d:%H}z.{domain_seg}.f{step:03d}.grib2"

        def _wave(host):
            return f"{host}/gfs.{d:%Y%m%d}/{d:%H}/wave/gridded/{stem}"

        idx = [".idx"]
        return {
            "aws": GribSource(_wave("https://noaa-gfs-bdp-pds.s3.amazonaws.com"), idx),
            "nomads": GribSource(
                _wave("https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"), idx
            ),
            "ftpprd": GribSource(
                _wave("https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod"), idx
            ),
        }
