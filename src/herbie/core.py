"""
You are looking under Herbie's hood, his engine.

TODO: Rename 'fxx' to 'step' and allow pandas-parsable timedelta string like "6h".
TODO: add `idx_to_df()` and `df_to_idx()` methods.
TODO: There are probably use cases for the `Path().suffixes` method
"""

import functools
import hashlib
import itertools
import json
import logging
import os
import subprocess
import urllib.request
import warnings
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from shutil import which
from typing import Literal, Optional, Union
from urllib.parse import urlparse

import cfgrib
import pandas as pd
import requests
import xarray as xr
from pyproj import CRS

import herbie.models as model_templates
from herbie import Path, config
from herbie.crs import get_cf_crs
from herbie.help import _search_help
from herbie.misc import ANSI

Datetime = Union[datetime, pd.Timestamp, str]

# NOTE: The config dict values are retrieved from __init__ and read
# from the file ${HOME}/.config/herbie/config.toml
# Path is imported from __init__ because it has my custom methods.

log = logging.getLogger(__name__)

# Location of wgrib2 command, if it exists. Required to make missing idx files.
wgrib2 = which("wgrib2")


def wgrib2_idx(grib2filepath: Path | str) -> str:
    """
    Produce the GRIB2 inventory index with wgrib2.

    Parameters
    ----------
    grib2filepath : Path or str
        Path to a grib2 file.

    Returns
    -------
    str
        The inventory output from wgrib2.

    Raises
    ------
    RuntimeError
        If wgrib2 command is not found.
    subprocess.CalledProcessError
        If wgrib2 command fails.
    """
    if not wgrib2:
        raise RuntimeError("wgrib2 command was not found.")

    try:
        p = subprocess.run(
            [wgrib2, "-s", str(grib2filepath)],
            capture_output=True,
            encoding="utf-8",
            check=True,
            text=True,
        )
        return p.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"wgrib2 failed with return code {e.returncode}: {e.stderr}"
        ) from e


def create_index_files(path: Union[Path, str], overwrite: bool = False) -> None:
    """Create an index file for all GRIB2 files in a directory.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to directory or file.
    overwrite : bool
        Overwrite index file if it exists.
    """
    path = Path(path)
    files = []
    if path.is_dir():
        # List all GRIB2 files in the directory
        files = list(path.rglob("*.grib2*"))
    elif path.is_file():
        # The path is a single file
        files = [path]

    if not files:
        raise ValueError(f"No grib2 files were found in {path}")

    for f in files:
        f_idx = Path(str(f) + ".idx")
        if not f_idx.exists() or overwrite:
            # Create an index using wgrib2's simple inventory option
            # if it doesn't already exist or if overwrite is True.
            index_data = wgrib2_idx(Path(f))
            with open(f_idx, "w+") as out_idx:
                out_idx.write(index_data)


class Herbie:
    """
    Locate GRIB2 file at one of the archive sources.

    Parameters
    ----------
    date : pandas-parsable datetime
        Model *initialization* datetime. If None, then must set
        ``valid_date``.
    valid_date : pandas-parsable datetime
        Model *valid* datetime. Must set when ``date`` is None.
    fxx : int or pandas-parsable timedelta (e.g. "6h")
        Forecast lead time *in hours*. Available lead times depend on
        the model type and model version.
    model : {'hrrr', 'hrrrak', 'rap', 'gfs', 'ecmwf', etc.}
        Model name as defined in the models template folder.
        CASE INSENSITIVE; e.g., "HRRR" is the same as "hrrr".
    product : {'sfc', 'prs', 'nat', 'subh', etc.}
        Output variable product file type. If not specified, will
        use first product in model template file. CASE SENSITIVE.
        For example, the HRRR model has these products:
        - ``'sfc'`` surface fields
        - ``'prs'`` pressure fields
        - ``'nat'`` native fields
        - ``'subh'`` subhourly fields
    member : None or int
        Some ensemble models (e.g. the future RRFS) will need to
        specify an ensemble member.
    priority : list or str
        List of model sources to get the data in the order of
        download priority. CASE INSENSITIVE. Some example data
        sources and the default priority order are listed below.
        - ``'aws'`` Amazon Web Services (Big Data Program)
        - ``'nomads'`` NOAA's NOMADS server
        - ``'google'`` Google Cloud Platform (Big Data Program)
        - ``'azure'`` Microsoft Azure (Big Data Program)
        - ``'pando'`` University of Utah Pando Archive (gateway 1)
        - ``'pando2'`` University of Utah Pando Archive (gateway 2)
    save_dir : str or pathlib.Path
        Location to save GRIB2 files locally. Default save directory
        is set in ``~/.config/herbie/config.cfg``.
    overwrite : bool
        If True, look for GRIB2 files on remote servers even if a local
        copy exists. If False (default), use the GRIB local copy if it
        exits. Note: it will still look for the idx file on the remote
        or try to generate the idx file if wgrib2 is installed.
    **kwargs
        Any other parameter needed to satisfy the conditions in the
        model template file (e.g., nest=2, other_label='run2')
    """

    config = config

    def __init__(
        self,
        date: Optional[Datetime] = None,
        *,
        valid_date: Optional[Datetime] = None,
        model: str = config["default"].get("model"),
        fxx: int = config["default"].get("fxx"),
        product: str = config["default"].get("product"),
        priority: Union[str, list[str]] = config["default"].get("priority"),
        save_dir: Union[Path, str] = config["default"].get("save_dir"),
        overwrite: bool = config["default"].get("overwrite", False),
        verbose: bool = config["default"].get("verbose", True),
        **kwargs,
    ):
        """Specify model output and find GRIB2 file at one of the sources."""
        self.fxx = fxx

        if isinstance(self.fxx, (str, pd.Timedelta)):
            # Convert pandas-parsable timedelta string to int in hours.
            self.fxx = pd.to_timedelta(fxx).round("1h").total_seconds() / 60 / 60
            self.fxx = int(self.fxx)

        if date:
            # User supplied `date`, which is the model initialization datetime.
            self.date = pd.to_datetime(date)
            self.valid_date = self.date + timedelta(hours=self.fxx)
        elif valid_date:
            # User supplied `valid_date`, which is the model valid datetime.
            self.valid_date = pd.to_datetime(valid_date)
            self.date = self.valid_date - timedelta(hours=self.fxx)
        else:
            raise ValueError("Must specify either `date` or `valid_date`")

        self.model = model.lower()
        self.product = product

        if self.model == "ecmwf":
            self.model = "ifs"
            warnings.warn(
                "`model='ecmwf'`is deprecated. Please use model='ifs' instead. Also, did you know you can also access `model='aifs'` too!",
                DeprecationWarning,
                stacklevel=2,
            )

        self.priority = priority
        self.save_dir = Path(save_dir).expand()
        self.overwrite = overwrite
        self.verbose = verbose

        # Some model templates may require kwargs not listed (e.g., `nest=`, `member=`).
        for key, value in kwargs.items():
            # TODO: Check if the kwarg is a config default.
            # TODO: e.g. if a user primarily works with RRFS, they may
            # TODO: want to configure "member" as a default argument.
            # You may also set IDX_SUFFIX as an argument.
            setattr(self, key, value)

        # Get details from the template of the specified model.
        # This attaches the details from the `models.<model>.template`
        # class to this Herbie object.
        # This line is equivalent to `model_templates.gfs.template(self)`.
        # I do it this way because the model name is a variable.
        # (see https://stackoverflow.com/a/7936588/2383070 for what I'm doing here)
        getattr(model_templates, self.model).template(self)

        # Specify the suffix for the inventory index files.
        # Default value is `.grib2.idx`, but some have weird suffix,
        # like archived RAP on NCEI are `.grb2.inv`.
        self.IDX_SUFFIX = getattr(self, "IDX_SUFFIX", [".grib2.idx"])

        # Specify the index file type. By default, Herbie assumes the
        # index file was created with wgrib2.
        # But for ecmwf files with index files created with eccodes
        # the index files are in a different style.
        self.IDX_STYLE = getattr(self, "IDX_STYLE", "wgrib2")

        self.search_help = _search_help(self.IDX_STYLE)

        if product is None:
            # The user didn't specify a product, so let's use the first
            # product in the model template.
            self.product = list(self.PRODUCTS)[0]
            log.info(f'`product` not specified. Will use "{self.product}".')
            # We need to rerun this so the sources have the new product value.
            getattr(model_templates, self.model).template(self)

        # Check the user input
        self._validate()

        self.product_description = self.PRODUCTS[self.product]

        # Ok, now we are ready to look for the GRIB2 file at each of the remote sources.
        # self.grib is the first existing GRIB2 file discovered.
        # self.idx is the first existing index file discovered.
        self.grib, self.grib_source = self.find_grib()
        self.idx, self.idx_source = self.find_idx()

        if verbose:
            # ANSI colors added for style points
            if any([self.grib is not None, self.idx is not None]):
                print(
                    "✅ Found",
                    f"┊ model={self.model}",
                    f"┊ {ANSI.italic}product={self.product}{ANSI.reset}",
                    f"┊ {ANSI.green}{self.date:%Y-%b-%d %H:%M UTC}{ANSI.bright_green} F{self.fxx:02d}{ANSI.reset}",
                    f"┊ {ANSI.orange}{ANSI.italic}GRIB2 @ {self.grib_source}{ANSI.reset}",
                    f"┊ {ANSI.orange}{ANSI.italic}IDX @ {self.idx_source}{ANSI.reset}",
                )
            else:
                print(
                    "💔 Did not find",
                    f"┊ model={self.model}",
                    f"┊ {ANSI.italic}product={self.product}{ANSI.reset}",
                    f"┊ {ANSI.green}{self.date:%Y-%b-%d %H:%M UTC}{ANSI.bright_green} F{self.fxx:02d}{ANSI.reset}",
                )

    def __repr__(self) -> str:
        """Representation in Notebook."""
        msg = (
            f"{ANSI.herbie} {self.model.upper()} model",
            f"{ANSI.italic}{self.product}{ANSI.reset} product initialized",
            f"{ANSI.green}{self.date:%Y-%b-%d %H:%M UTC}{ANSI.bright_green} F{self.fxx:02d}{ANSI.reset}",
            f"┊ {ANSI.orange}{ANSI.italic}source={self.grib_source}{ANSI.reset}",
        )
        return " ".join(msg)

    def __str__(self) -> str:
        """When Herbie class object is printed, print all properties."""
        # * Keep this simple so it runs fast.
        msg = (f"║HERBIE╠ {self.model.upper()}:{self.product}",)
        return " ".join(msg)

    def __bool__(self) -> bool:
        """Herbie evaluated True if the GRIB file exists."""
        return bool(self.grib)

    def help(self) -> None:
        """Print help message if available."""
        if hasattr(self, "HELP"):
            HELP = self.HELP.strip().replace("\n", "\n│ ")
        else:
            HELP = "│"
        print("╭─ Herbie ────────────────────────────────")
        print(f"│ Help for model='{self.model}'")
        print("│ ")
        print(f"│ {self.DESCRIPTION}")
        for key, value in self.DETAILS.items():
            print(f"│  {key}: {value}")
        print("│")
        print(f"│ {HELP}")
        print("│")
        print("╰─────────────────────────────────────────")

    def tell_me_everything(self) -> None:
        """Print all the attributes of the Herbie object."""
        msg = []
        for i in dir(self):
            if isinstance(getattr(self, i), (int, str, dict)):
                if not i.startswith("__"):
                    msg.append(f"self.{i}={getattr(self, i)}")
        msg = "\n".join(msg)
        print(msg)

    def __logo__(self) -> None:
        """For Fun, show the Herbie Logo."""
        print(ANSI.ascii)

    def _validate(self) -> None:
        """Validate the Herbie class input arguments."""
        # Accept model alias
        if self.model.lower() == "alaska":
            self.model = "hrrrak"

        _models = {m for m in dir(model_templates) if not m.startswith("__")}
        _products = set(self.PRODUCTS)

        assert self.date < pd.Timestamp.utcnow().tz_localize(None), (
            "🔮 `date` cannot be in the future."
        )
        assert self.model in _models, f"`model` must be one of {_models}"
        assert self.product in _products, f"`product` must be one of {_products}"

        if isinstance(self.IDX_SUFFIX, str):
            self.IDX_SUFFIX = [self.IDX_SUFFIX]

        if isinstance(self.priority, str):
            self.priority = [self.priority]

        if self.priority is not None:
            self.priority = [i.lower() for i in self.priority]

            # Don't look for data from NOMADS if requested date is earlier
            # than 14 days ago. NOMADS doesn't keep data that old,
            # (I think this is true of all models).
            if "nomads" in self.priority:
                expired = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(
                    days=14
                )
                if self.date < expired:
                    self.priority.remove("nomads")

    def _ping_pando(self) -> None:
        """Pinging the Pando server before downloading can prevent a bad handshake."""
        try:
            requests.head("https://pando-rgw01.chpc.utah.edu/")
        except Exception:
            print("🤝🏻⛔ Bad handshake with pando? Am I able to move on?")
            pass

    def _check_grib(self, url: str, min_content_length: int = 10) -> bool:
        """
        Check that the GRIB2 URL exist and is of useful length.

        Parameters
        ----------
        url : str
            Full URL path to the GRIB file
        min_content_length : int
            The HTTP header content-length in bytes.
            Used to check a file is of useful size. This was once set to
            1_000_000 (1 MB), but there was an issue with NOMADS not
            providing this right (see #114). I decreased to 10 and
            essentially turned off this check.
        """
        head = requests.head(url)
        check_exists = head.ok
        if check_exists and "Content-Length" in head.raw.info():
            check_content = int(head.raw.info()["Content-Length"]) > min_content_length
            return check_exists and check_content
        else:
            return False

    def _check_idx(self, url: str, verbose: bool = False) -> tuple[bool, Optional[str]]:
        """Check if an index file exist for the GRIB2 URL."""
        # To check inventory files with slightly different URL structure
        # we will loop through the IDX_SUFFIX.

        if verbose:
            print(f"🐜 {self.IDX_SUFFIX=}")

        # Initialize variable to avoid UnboundLocalError
        idx_exists = False

        # Loop through IDX_SUFFIX options until we find one that exists
        for i in self.IDX_SUFFIX:
            if Path(url).suffix in {".grb", ".grib", ".grb2", ".grib2"}:
                idx_url = url.rsplit(".", maxsplit=1)[0] + i
            else:
                idx_url = url + i

            try:
                if "blob.core.windows.net" in idx_url:
                    dl_url = (
                        "https://planetarycomputer.microsoft.com/api/sas/v1/sign?href="
                        + idx_url
                    )
                    response = requests.get(dl_url)
                    idx_url = response.json()["href"]
                idx_exists = requests.head(idx_url).ok
            except Exception as e:
                if verbose:
                    print(
                        f"Unable to get index file from {idx_url} due to error {str(e)}"
                    )

            if verbose:
                print(f"🐜 {idx_url=}")
                print(f"🐜 {idx_exists=}")
            if idx_exists:
                return idx_exists, idx_url

        if verbose:
            print(
                "⚠ Herbie didn't find any inventory files that",
                f"exists from {self.IDX_SUFFIX}",
            )
        return False, None

    def find_grib(self) -> tuple[Optional[Union[Path, str]], Optional[str]]:
        """Find a GRIB file from the archive sources.

        Returns
        -------
        1) The URL or pathlib.Path to the GRIB2 files that exists
        2) The source of the GRIB2 file
        """
        # But first, check if the GRIB2 file exists locally.
        local_grib = self.get_localFilePath()
        if local_grib.exists() and not self.overwrite:
            return local_grib, "local"

        # If priority list is set, we want to search SOURCES in that
        # priority order. If priority is None, then search all SOURCES
        # in the order given by the model template file.
        # NOTE: A source from the template will not be used if it is not
        # included in the priority list.
        if self.priority is not None:
            self.SOURCES = {
                key: self.SOURCES[key] for key in self.priority if key in self.SOURCES
            }

        # Ok, NOW we are ready to search for the remote GRIB2 files...
        for source in self.SOURCES:
            if "pando" in source:
                # Sometimes pando returns a bad handshake. Pinging
                # pando first can help prevent that.
                self._ping_pando()

            # Get the file URL for the source and determine if the
            # GRIB2 file and the index file exist. If found, store the
            # URL for the GRIB2 file and the .idx file.
            if "azure" in source:
                download_url = (
                    "https://planetarycomputer.microsoft.com/api/sas/v1/sign?href="
                    + self.SOURCES[source]
                )
                response = requests.get(download_url)
                grib_url = response.json()["href"]
            else:
                grib_url = self.SOURCES[source]
            if source.startswith("local"):
                grib_path = Path(grib_url)
                if grib_path.exists():
                    return (grib_path, source)
            elif self._check_grib(grib_url):
                return (grib_url, source)

        return (None, None)

    def find_idx(self) -> tuple[Optional[Union[Path, str]], Optional[str]]:
        """Find an index file for the GRIB file."""

        # But first, if overwrite is False, then check if the GRIB2 inventory file exists locally.
        if not self.overwrite:
            local_grib = self.get_localFilePath()
            for suffix in self.IDX_SUFFIX:
                # There is no easy way to know if the index suffix needs to be appended or overwrite the grib suffix.
                # Hence there is a need to do various checks to verify if the index file exists locally or not.

                # This is the case of GFS, where the grib file ends with ".grb2" and the index file is ".grb2.inv"
                # The index suffix needs to overwrite the grib file suffix, now ending in ".grb2.inv"
                if suffix.startswith(local_grib.suffix):
                    local_idx = local_grib.with_suffix(suffix)

                # This is the case of GFS, where the grib file ends with ".f000" and the index file is ".idx"
                # The index suffix needs to be appended to the grib file suffix, now ending in ".f000.idx"
                else:
                    local_idx = local_grib.with_suffix(local_grib.suffix + suffix)

                if local_idx.exists() and not self.overwrite:
                    return (local_idx, "local")

                # If the index file does not exists locally, we will need to try another variation of the index file name.
                # This is the case of IFS, where the grib file ends with ".grib2" and the index file is ".index"
                # The index suffix needs to overwrite the grib file suffix, now ending in ".index"
                else:
                    local_idx = local_grib.with_suffix(suffix)
                    if local_idx.exists() and not self.overwrite:
                        return (local_idx, "local")

        # If priority list is set, we want to search SOURCES in that
        # priority order. If priority is None, then search all SOURCES
        # in the order given by the model template file.
        # NOTE: A source from the template will not be used if it is not
        # included in the priority list.
        if self.priority is not None:
            self.SOURCES = {
                key: self.SOURCES[key] for key in self.priority if key in self.SOURCES
            }

        # Ok, NOW we are ready to search for the remote GRIB2 files...
        for source in self.SOURCES:
            if "pando" in source:
                # Sometimes pando returns a bad handshake. Pinging
                # pando first can help prevent that.
                self._ping_pando()

            # Get the file URL for the source and determine if the
            # GRIB2 file and the index file exist. If found, store the
            # URL for the GRIB2 file and the .idx file.
            if "azure" in source:
                download_url = (
                    "https://planetarycomputer.microsoft.com/api/sas/v1/sign?href="
                    + self.SOURCES[source]
                )
                response = requests.get(download_url)
                grib_url = response.json()["href"]
            else:
                grib_url = self.SOURCES[source]

            if source.startswith("local"):
                local_grib = Path(grib_url)
                local_idx = local_grib.with_suffix(self.IDX_SUFFIX[0])
                if local_idx.exists():
                    return (local_idx, "local")
            else:
                idx_exists, idx_url = self._check_idx(self.SOURCES[source])

                if idx_exists:
                    return (idx_url, source)

        return (None, None)

    @property
    def get_remoteFileName(self, source: Optional[str] = None) -> str:
        """Predict remote file name."""
        if source is None:
            if hasattr(self, "grib_source") and self.grib_source != "local":
                source = self.grib_source
            else:
                # Just pick the first source in the template
                # Note: this might not always be the best approach
                # the file names are not consistent between sources.
                source = list(self.SOURCES)[0]
        return self.SOURCES[source].split("/")[-1]

    @property
    def get_localFileName(self) -> str:
        """Predict the local file name."""
        return self.LOCALFILE

    def get_localFilePath(
        self, search: Optional[str] = None, *, searchString=None
    ) -> Path:
        """Get full path to the local file."""
        # TODO: Remove this check for searString eventually
        if searchString is not None:
            warnings.warn(
                "The argument `searchString` was renamed `search`. Please update your scripts.",
                DeprecationWarning,
                stacklevel=2,
            )
            search = searchString

        # Predict the localFileName from the first model template SOURCE.
        localFilePath = (
            self.save_dir / self.model / f"{self.date:%Y%m%d}" / self.get_localFileName
        )

        # Check if any sources in a model template are "local"
        # (i.e., a custom template file)
        if any([i.startswith("local") for i in self.SOURCES.keys()]):
            localFilePath = next(
                (
                    Path(self.SOURCES[i])
                    for i in self.SOURCES
                    if i.startswith("local") and Path(self.SOURCES[i]).exists()
                ),
                localFilePath,
            )

        if search is not None:
            # Reassign the index DataFrame with the requested search
            idx_df = self.inventory(search)

            # ======================================
            # Make a unique filename for the subset

            # Get a list of all GRIB message numbers. We will use this
            # in the output file name as a unique identifier.
            all_grib_msg = "-".join([f"{i:g}" for i in idx_df.index])

            # To prevent "filename too long" error, create a hash to
            # that represents the file name and subseted variables to
            # shorten the name.

            # I want the files to still be sorted by date, fxx, and
            # subset fields, so include three separate hashes to similar
            # files will be sorted together.

            hash_date = hashlib.blake2b(
                f"{self.date:%Y%m%d%H%M}".encode(), digest_size=1
            ).hexdigest()

            hash_fxx = hashlib.blake2b(
                f"{self.fxx}".encode(), digest_size=1
            ).hexdigest()

            hash_label = hashlib.blake2b(
                all_grib_msg.encode(), digest_size=2
            ).hexdigest()

            # Prepend the filename with the hash label to distinguish it
            # from the full file. The hash label is a cryptic
            # representation of the GRIB messages in the subset.
            localFilePath = (
                localFilePath.parent
                / f"subset_{hash_date}{hash_fxx}{hash_label}__{localFilePath.name}"
            )

        return localFilePath

    def get_localIndexFilePath(self) -> Path:
        """Get full path to the local index file."""

        # Get the local file path, which creates the directory structure
        local_file_path = self.get_localFilePath()

        # Get the directory in the local file path
        dir_path = os.path.dirname(local_file_path)

        # Get the filename from the index URL path
        index_filename = os.path.basename(urlparse(self.idx).path)

        # Create new path with the index file name
        index_file_path = os.path.join(dir_path, index_filename)

        return index_file_path

    @functools.cached_property
    def index_as_dataframe(self) -> pd.DataFrame:
        """Read and cache the full index file."""
        if self.idx_source is None and self.grib_source == "local" and wgrib2:
            # Generate IDX inventory with wgrib2
            self.idx = StringIO(wgrib2_idx(self.get_localFilePath()))
            self.idx_source = "generated"
            self.IDX_STYLE = "wgrib2"
        elif self.idx is None:
            if self.grib_source == "local":
                # Use wgrib2 to get the index file if the file is local
                log.info("🧙🏻‍♂️ I'll use wgrib2 to create the missing index file.")
                self.idx = StringIO(wgrib2_idx(self.get_localFilePath()))
                self.IDX_STYLE = "wgrib2"
            else:
                raise ValueError(
                    f"\nNo index file was found for {self.grib}\n"
                    f"Download the full file first (with `H.download()`).\n"
                    f"You will need to remake the Herbie object (H = `Herbie()`)\n"
                    f"or delete this cached property: `del H.index_as_dataframe()`"
                )
        if self.idx is None:
            raise ValueError(f"No index file found for {self.grib}.")

        if self.IDX_STYLE == "wgrib2":
            # Sometimes idx lines end in ':', other times it doesn't (in some Pando files).
            # https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20180101/hrrr.t00z.wrfsfcf00.grib2.idx
            # https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20210101/conus/hrrr.t00z.wrfsfcf00.grib2.idx
            # Sometimes idx has more than the standard messages
            # https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20210711/13/core/blend.t13z.core.f001.co.grib2.idx
            if self.idx_source in ["local", "generated"]:
                read_this_idx = self.idx
            else:
                read_this_idx = None
                if self.verbose:
                    print(f"Downloading inventory file from {self.idx=}")
                response = requests.get(self.idx)
                if response.status_code != 200:
                    response.raise_for_status()
                    response.close()
                    raise ValueError(
                        f"\nCant open index file {self.idx}\n"
                        f"Download the full file first (with `H.download()`).\n"
                        f"You will need to remake the Herbie object (H = `Herbie()`)\n"
                        f"or delete this cached property: `del H.index_as_dataframe()`"
                    )

                read_this_idx = StringIO(response.text)
                response.close()

                index_filepath = self.get_localIndexFilePath()
                os.makedirs(os.path.dirname(index_filepath), exist_ok=True)

                with open(index_filepath, "w") as file:
                    file.write(read_this_idx.read())
                    # reset the cursor to the beggining of the StringIO
                    read_this_idx.seek(0)

            df = pd.read_csv(
                read_this_idx,
                sep=":",
                names=[
                    "grib_message",
                    "start_byte",
                    "reference_time",
                    "variable",
                    "level",
                    "forecast_time",
                    "?",
                    "??",
                    "???",
                ],
            )

            # Format the DataFrame
            df["reference_time"] = pd.to_datetime(
                df.reference_time, format="d=%Y%m%d%H"
            )
            df["valid_time"] = df["reference_time"] + pd.to_timedelta(f"{self.fxx}h")
            df["start_byte"] = df["start_byte"].astype(int)
            df["end_byte"] = df["start_byte"].shift(-1) - 1
            df["range"] = df.apply(
                lambda x: f"{x.start_byte:.0f}-{x.end_byte:.0f}".replace("nan", ""),
                axis=1,
            )
            df = df.reindex(
                columns=[
                    "grib_message",
                    "start_byte",
                    "end_byte",
                    "range",
                    "reference_time",
                    "valid_time",
                    "variable",
                    "level",
                    "forecast_time",
                    "?",
                    "??",
                    "???",
                ]
            )

            df = df.dropna(how="all", axis=1)

            df["search_this"] = (
                df.loc[:, "variable":]
                .astype(str)
                .apply(
                    lambda x: ":" + ":".join(x).rstrip(":").replace(":nan:", ":"),
                    axis=1,
                )
            )

        if self.IDX_STYLE == "eccodes":
            # eccodes keywords explained here:
            # https://confluence.ecmwf.int/display/UDOC/Identification+keywords

            if self.idx_source in ["local"]:
                with open(self.idx, "r") as file:
                    read_this_idx = StringIO(file.read())
            else:
                if self.verbose:
                    print(f"Downloading inventory file from {self.idx=}")
                response = requests.get(self.idx)
                if response.status_code != 200:
                    response.raise_for_status()
                    response.close()
                    raise ValueError(
                        f"\nCant open index file {self.idx}\n"
                        f"Download the full file first (with `H.download()`).\n"
                        f"You will need to remake the Herbie object (H = `Herbie()`)\n"
                        f"or delete this cached property: `del H.index_as_dataframe()`"
                    )

                read_this_idx = StringIO(response.text)
                response.close()

                index_filepath = self.get_localIndexFilePath()
                os.makedirs(os.path.dirname(index_filepath), exist_ok=True)

                with open(index_filepath, "w") as file:
                    file.write(read_this_idx.read())
                    # reset the cursor to the beggining of the StringIO
                    read_this_idx.seek(0)

            idxs = [json.loads(x) for x in read_this_idx.getvalue().split("\n") if x]
            df = pd.DataFrame(idxs)

            # Format the DataFrame
            df.index = df.index.rename("grib_message")
            df.index += 1
            df = df.reset_index()
            df["start_byte"] = df["_offset"]
            df["end_byte"] = df["_offset"] + df["_length"]
            df["range"] = df.start_byte.astype(str) + "-" + df.end_byte.astype(str)
            df["reference_time"] = pd.to_datetime(
                df.date + df.time, format="%Y%m%d%H%M"
            )
            df["step"] = pd.to_timedelta(df.step.astype(int), unit="h")
            df["valid_time"] = df.reference_time + df.step

            df = df.reindex(
                columns=[
                    "grib_message",
                    "start_byte",
                    "end_byte",
                    "range",
                    "reference_time",
                    "valid_time",
                    "step",
                    # ---- Used for search ------------------------------
                    "param",  # parameter field (variable)
                    "levelist",  # level
                    "levtype",  # sfc=surface, pl=pressure level, pt=potential vorticity
                    "number",  # model number (used in ensemble products)
                    "domain",  # g=global
                    "expver",  # experiment version
                    "class",  # classification (od=routing operations, rd=research, )
                    "type",  # fc=forecast, an=analysis,
                    "stream",  # oper=operationa, wave=wave, ef/enfo=ensemble,
                ]
            )

            df["search_this"] = (
                df.loc[:, "param":]
                .astype(str)
                .apply(
                    lambda x: ":" + ":".join(x).rstrip(":").replace(":nan:", ":"),
                    axis=1,
                )
            )

        # Attach some attributes
        df.attrs = dict(
            url=self.idx,
            source=self.idx_source,
            description="Inventory index file for the GRIB2 file.",
            model=self.model,
            product=self.product,
            lead_time=self.fxx,
            datetime=self.date,
        )

        return df

    def inventory(
        self,
        search: Optional[str] = None,
        *,
        searchString=None,
        verbose: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Inspect the GRIB2 file contents by reading the index file.

        This reads index files created with the wgrib2 utility.

        Parameters
        ----------
        search : str
            Filter dataframe by a search regular expression.
            Searches for strings in the index file lines, specifically
            the variable, level, and forecast_time columns.
            Execute ``_search_help()`` for examples of a good
            search.

            Read more in the user guide at
            https://herbie.readthedocs.io/en/latest/user_guide/tutorial/search.html
        verbose : None, bool
            If True, then print a help message if no messages are found.
            If False, does not print a help message if no messages are found.
            If None (default), then verbose is set in the Herbie.__init__.

        Returns
        -------
        A Pandas DataFrame of the index file.

        """
        df = self.index_as_dataframe

        # TODO: Remove this eventually
        if searchString is not None:
            warnings.warn(
                "The argument `searchString` was renamed `search`. Please update your scripts.",
                DeprecationWarning,
                stacklevel=2,
            )
            search = searchString

        # This overrides the verbose specified in __init__
        if verbose is not None:
            self.verbose = verbose

        # Filter DataFrame by regex search
        if search not in [None, ":"]:
            logic = df.search_this.str.contains(search)
            if (logic.sum() == 0) and verbose:
                print(
                    f"No GRIB messages found. There might be something wrong with {search=}"
                )
                print(_search_help(kind=self.IDX_STYLE))
            df = df.loc[logic]
        return df

    def download(
        self,
        search: Optional[str] = None,
        *,
        searchString=None,
        source: Optional[str] = None,
        save_dir: Optional[Union[str, Path]] = None,
        overwrite: Optional[bool] = None,
        verbose: Optional[bool] = None,
        errors: Literal["warn", "raise"] = "warn",
    ) -> Path:
        """
        Download file from source.

        TODO: When we download a full file, the value of self.grib and
        TODO:   self.grib_source should change to represent the local file.

        Subsetting by variable follows the same principles described here:
        https://www.cpc.ncep.noaa.gov/products/wesley/fast_downloading_grib.html

        Parameters
        ----------
        search : str
            If None, download the full file. Else, use regex to subset
            the file by specific variables and levels.
            Read more in the user guide:
            https://herbie.readthedocs.io/en/latest/user_guide/tutorial/search.html
        source : {'nomads', 'aws', 'google', 'azure', 'pando', 'pando2'}
            If None, download GRIB2 file from self.grib2 which is
            the first location the GRIB2 file was found from the
            priority lists when this class was initialized. Else, you
            may specify the source to force downloading it from a
            different location.
        save_dir : str or pathlib.Path
            Location to save the model output files.
            If None, uses the default or path specified in __init__.
            Else, changes the path files are saved.
        overwrite : bool
            If True, overwrite existing files. Default will skip
            downloading if the full file exists. Not applicable when
            when search is not None because file subsets might
            be unique.
        errors : {'warn', 'raise'}
            When an error occurs, send a warning or raise a value error.

        """

        def _reporthook(a, b, c):
            """
            Print download progress in megabytes.

            Parameters
            ----------
            a : Chunk number
            b : Maximum chunk size
            c : Total size of the download
            """
            chunk_progress = a * b / c * 100
            total_size_MB = c / 1000000.0
            if verbose:
                print(
                    f"\r🚛💨  Download Progress: {chunk_progress:.2f}% of {total_size_MB:.1f} MB\r",
                    end="",
                )

        def subset(search, outFile, verbose=True):
            """Download/extract a subset specified by the regex search."""
            grib_source = self.grib

            # Check if the source is a local file
            is_local = isinstance(grib_source, Path) or (
                isinstance(grib_source, str)
                and not grib_source.startswith(("http://", "https://"))
            )

            if verbose:
                source_desc = f"local file {grib_source}" if is_local else grib_source
                print(f"📇 Download subset: {self.__repr__()}\n from {source_desc}")

            idx_df = self.inventory(search).copy()

            if len(idx_df) == 0:
                return

            idx_df["download_groups"] = idx_df.grib_message.diff().ne(1).cumsum()

            # Process subsets of each group
            for i, subset_group in idx_df.groupby("download_groups"):
                if verbose:
                    action = "Extract" if is_local else "Download"
                    print(f"{action} subset group {i} ({len(subset_group)} variables)")

                if verbose:
                    for _, row in subset_group.iterrows():
                        print(
                            f"  {row.grib_message:<3g} {ANSI.orange}{row.search_this}{ANSI.reset}"
                        )

                start_byte = subset_group.start_byte.min()

                end_byte = subset_group.end_byte.max()

                if end_byte - start_byte < 0:
                    if verbose:
                        print("  ERROR: Invalid byte range; Skip message.")
                    continue

                try:
                    # Get the data (either from local file or remote URL)
                    if is_local:
                        # Read from local file
                        with open(grib_source, "rb") as src:
                            if verbose:
                                print(
                                    f"Read local file: bytes={int(start_byte)}-{int(end_byte) if not pd.isna(end_byte) else ''}"
                                )
                            src.seek(int(start_byte))
                            if pd.isna(end_byte):
                                data = src.read()
                            else:
                                data = src.read(int(end_byte) - int(start_byte) + 1)
                    else:
                        # Download from remote URL
                        headers = {
                            "Range": f"bytes={int(start_byte)}-{int(end_byte) if not pd.isna(end_byte) else ''}"
                        }
                        if verbose:
                            print(f"Download subset: {headers=}")
                        response = requests.get(
                            grib_source,
                            headers=headers,
                            timeout=30,
                        )
                        response.raise_for_status()
                        data = response.content

                    # Write or append to output file
                    mode = "wb" if i == 1 else "ab"
                    with open(outFile, mode) as f:
                        f.write(data)

                    if verbose:
                        print(
                            f"  ✓ Processed bytes {int(start_byte)}-{int(end_byte) if not pd.isna(end_byte) else ''}"
                        )

                except (IOError, requests.RequestException) as e:
                    if verbose:
                        print(f"  ✗ Failed to process: {e}")
                    raise RuntimeError(f"Processing failed: {e}") from e

            if verbose:
                print(f"💾 Saved the subset to {outFile}")

        # TODO: Remove this eventually
        if searchString is not None:
            warnings.warn(
                "The argument `searchString` was renamed `search`. Please update your scripts.",
                DeprecationWarning,
                stacklevel=2,
            )
            search = searchString

        # This overrides the save_dir specified in __init__
        if save_dir is not None:
            self.save_dir = Path(save_dir).expand()

        if not hasattr(Path(self.save_dir).expand(), "exists"):
            self.save_dir = Path(self.save_dir).expand()

        # If the file exists in the localPath and we don't want to
        # overwrite, then we don't need to download it.
        outFile = self.get_localFilePath(search)

        if save_dir is not None:
            # Looks like the save_dir was changed.
            outFile = (
                self.save_dir.expand()
                / self.model
                / f"{self.date:%Y%m%d}"
                / outFile.name
            )

        # This overrides the overwrite specified in __init__
        if overwrite is not None:
            self.overwrite = overwrite

        # This overrides the verbose specified in __init__
        if verbose is not None:
            self.verbose = verbose

        if outFile.exists() and not self.overwrite:
            if verbose:
                print(f"🌉 Already have local copy --> {outFile}")
            return outFile

        if (
            self.overwrite
            and self.grib_source
            and self.grib_source.startswith("local")
            and search in [None, ":"]
        ):
            # Search for the grib files on the remote archives again
            # Only do this for full file downloads, not subsets
            self.grib, self.grib_source = self.find_grib()
            self.idx, self.idx_source = self.find_idx()
            print(f"Overwrite local file with file from [{self.grib_source}]")

        # Check that data exists
        if self.grib is None:
            msg = f"🦨 GRIB2 file not found: {self.model=} {self.date=} {self.fxx=}"
            if errors == "warn":
                log.warning(msg)
                return  # Can't download anything without a GRIB file URL.
            elif errors == "raise":
                raise ValueError(msg)
        if self.idx is None and search is not None:
            msg = f"🦨 Index file not found; cannot download subset: {self.model=} {self.date=} {self.fxx=}"
            if errors == "warn":
                log.warning(
                    msg + " I will download the full file because I cannot subset."
                )
            elif errors == "raise":
                raise ValueError(msg)

        if source is not None:
            # Force download from a specified source and not from first in priority
            self.grib = self.SOURCES[source]

        # Create directory if it doesn't exist
        if not outFile.parent.is_dir():
            outFile.parent.mkdir(parents=True, exist_ok=True)
            print(f"👨🏻‍🏭 Created directory: [{outFile.parent}]")

        # ===============
        # Do the Download
        # ===============
        if search in [None, ":"] or self.idx is None:
            # Download the full file from remote source
            urllib.request.urlretrieve(self.grib, outFile, _reporthook)

            original_source = self.grib

            self.grib = outFile
            # self.grib_source = "local"  # ?? Why did I turn this off?

            if verbose:
                print(
                    f"✅ Success! Downloaded {self.model.upper()} from \033[38;5;202m{self.grib_source:20s}\033[0m\n\tsrc: {original_source}\n\tdst: {outFile}"
                )

        else:
            # Download a subset of the file
            subset(search, outFile, verbose=verbose)

        return outFile

    def xarray(
        self,
        search: Optional[str] = None,
        *,
        searchString=None,
        backend_kwargs: dict = {},
        remove_grib: bool = True,
        _use_pygrib_for_crs: bool = False,
        **download_kwargs,
    ) -> xr.Dataset:
        """
        Open GRIB2 data as xarray DataSet.

        Parameters
        ----------
        search : str
            Variables to read into xarray Dataset
        remove_grib : bool
            If True, grib file will be removed ONLY IF it didn't exist
            before we downloaded it.
        _use_pygrib_for_crs : bool
            If you have pygrib, you can use it to extract the CRS
            information instead of using values extracted from cfgrib
            by Herbie.
        """
        # TODO: Remove this eventually
        if searchString is not None:
            warnings.warn(
                "The argument `searchString` was renamed `search`. Please update your scripts.",
                DeprecationWarning,
                stacklevel=2,
            )
            search = searchString

        download_kwargs = {**dict(overwrite=False), **download_kwargs}

        local_file = self.get_localFilePath(search)

        if "save_dir" in download_kwargs:
            # Looks like the save_dir was changed.
            self.save_dir = Path(download_kwargs["save_dir"]).expand()
            local_file = (
                self.save_dir.expand()
                / self.model
                / f"{self.date:%Y%m%d}"
                / local_file.name
            )

        #!==============================================================
        #!                        ⚠ CRITICAL ⚠
        #!==============================================================
        #! File cannot be removed if it previously existed.
        #! (We don't want to remove previously downloaded content).
        if local_file.exists() and remove_grib:
            warnings.warn("Will not remove GRIB file because it previously existed.")
            remove_grib = False
        #! File can only be be removed if it is a subsetted file.
        #! (We don't want to remove full local files.)
        if search is None and remove_grib:
            warnings.warn(
                "Will not remove GRIB file because Herbie will only remove subsetted files (not full files)."
            )
            remove_grib = False
        #!==============================================================

        # Download file if local file does not exists
        if not local_file.exists() or download_kwargs["overwrite"]:
            self.download(search=search, **download_kwargs)

        # Backend kwargs for cfgrib
        backend_kwargs.setdefault("indexpath", "")
        backend_kwargs.setdefault(
            "read_keys",
            [
                "parameterName",
                "parameterUnits",
                "stepRange",
                "uvRelativeToGrid",
                "shapeOfTheEarth",
                "orientationOfTheGridInDegrees",
                "southPoleOnProjectionPlane",
                "LaDInDegrees",
                "LoVInDegrees",
                "Latin1InDegrees",
                "Latin2InDegrees",
            ],
        )
        backend_kwargs.setdefault("errors", "raise")

        # Use cfgrib.open_datasets, just in case there are multiple "hypercubes"
        # for what we requested.
        Hxr = cfgrib.open_datasets(
            local_file,
            backend_kwargs=backend_kwargs,
            decode_timedelta=True,
        )

        for ds in Hxr:
            # Need model attribute before using get_cf_crs
            ds.attrs["model"] = str(self.model)

        # Get CF convention coordinate reference system (crs) information.
        # NOTE: Assumes the projection is the same for all variables.
        if _use_pygrib_for_crs:
            # Get CF grid projection information with pygrib and pyproj because
            # this is something cfgrib doesn't do (https://github.com/ecmwf/cfgrib/issues/251)
            import pygrib

            with pygrib.open(str(local_file)) as grb:
                msg = grb.message(1)
                cf_params = CRS(msg.projparams).to_cf()

            # Funny stuff with polar stereographic (https://github.com/pyproj4/pyproj/issues/856)
            # TODO: Is there a better way to handle this? What about south pole?
            if cf_params["grid_mapping_name"] == "polar_stereographic":
                cf_params["latitude_of_projection_origin"] = cf_params.get(
                    "latitude_of_projection_origin", 90
                )
        else:
            cf_params = get_cf_crs(Hxr[0])

        # Here I'm looping over each dataset in the list returned by cfgrib
        for ds in Hxr:
            # ----------------
            # Add some details
            # ----------------
            # Note: all attributes should still work with the `ds.to_netcdf()` method.
            ds.attrs["model"] = str(self.model)
            ds.attrs["product"] = str(self.product)
            ds.attrs["description"] = self.DESCRIPTION
            ds.attrs["remote_grib"] = str(self.grib)
            ds.attrs["local_grib"] = str(local_file)
            ds.attrs["search"] = str(search)

            # ----------------------
            # Attach CF grid mapping
            # ----------------------
            # http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#appendix-grid-mappings
            ds.coords["gribfile_projection"] = None
            ds.coords["gribfile_projection"].attrs = cf_params
            ds.coords["gribfile_projection"].attrs["long_name"] = (
                f"{self.model.upper()} model grid projection"
            )

            # Assign this grid_mapping for all variables
            for var in list(ds):
                ds[var].attrs["grid_mapping"] = "gribfile_projection"

        if remove_grib:
            # Load the datasets into memory before removing the file
            Hxr = [ds.load() for ds in Hxr]
            _ = [ds.close() for ds in Hxr]
            local_file.unlink()

        if len(Hxr) == 1:
            return Hxr[0]
        else:
            # cfgrib returned multiple hypercubes.
            try:
                # Handle case where HRRR subh returns multiple hypercubes (see #73)
                data_vars = set(itertools.chain(*[list(i) for i in Hxr]))
                data_vars.remove("gribfile_projection")
                Hxr = xr.concat(Hxr, dim="step", data_vars=data_vars)
            except Exception:
                if self.verbose:
                    print(
                        f"Note: Returning a list of [{len(Hxr)}] xarray.Datasets because cfgrib opened with multiple hypercubes."
                    )
            return Hxr

    def terrain(self, water_masked: bool = True) -> xr.Dataset:
        """Shortcut method to return model terrain as an xarray.Dataset."""
        ds = self.xarray(":(?:HGT|LAND):surface")
        if water_masked:
            ds["orog"] = ds.orog.where(ds.lsm > 0)
        return ds
