#!/usr/bin/env python3

## Brian Blaylock
## May 6, 2022

"""

===============================
Herbie: Retrieve NWP Model Data
===============================

Herbie is your model output download assistant with a mind of his own!
Herbie might look small on the outside, but he has a big heart on the
inside and will get you to the
`finish line <https://www.youtube.com/watch?v=4XWufUZ1mxQ&t=189s>`_.
Happy racing! 🏁

`📓 Documentation <https://herbie.readthedocs.io/>`_

With Herbie's API, you can search and download GRIB2 model output files
from different archive sources for the High-Resolution Rapid Refresh
(HRRR) HRRR-Alaska, Rapid Refresh (RAP), Global Forecast System (GFS),
and others.

Herbie looks for GRIB2 model output data from NOMADS, NOAA's Big Data
Project partners (Amazon Web Services, Google Cloud Platform, and
Microsoft Azure), and the CHPC Pando archive at the University of Utah.

Herbie supports subsetting of GRIB2 files by individual GRIB
messages (i.e. variable and level) when the index (.idx) file exist and
help you open them with xarray/cfgrib.

Herbie is extendable to support other models. Simply create a template
file in the ``herbie/models`` directory and make a pull-request.

For more details, see https://herbie.readthedocs.io/user_guide/data_sources.html


TODO: Rename 'searchString' to 'subset' (and rename subset function to??) - REJECTED, for now
TODO: Rename 'fxx' to 'lead' and allow pandas-parsable timedelta string like "6H".
TODO: add `idx_to_df()` and `df_to_idx()` methods.
TODO: There are probably use cases for the `Path().suffixes` method
"""
import functools
import hashlib
import itertools
import json
import logging
import os
import sys
import urllib.request
import warnings
from datetime import datetime, timedelta
from io import StringIO

import cfgrib
import pandas as pd
import pygrib
import requests
import xarray as xr
from pyproj import CRS
import subprocess
from shutil import which

import herbie.models as model_templates
from herbie import Path, config
from herbie.help import _searchString_help
from herbie.misc import ANSI

# NOTE: The config dict values are retrieved from __init__ and read
# from the file ${HOME}/.config/herbie/config.toml
# Path is imported from __init__ because it has my custom methods.

try:
    # Load custom xarray accessors
    import herbie.accessors
except:
    warnings.warn(
        "herbie xarray accessors could not be imported."
        "Probably missing a dependency like MetPy."
        "If you want to use these functions, try"
        "`pip install metpy`"
    )
    pass

log = logging.getLogger(__name__)

# Location of wgrib2 command, if it exists
wgrib2 = which("wgrib2")


def wgrib2_idx(grib2filepath):
    """
    Produce the GRIB2 inventory index with wgrib2.

    Parameters
    ----------
    grib2filepath : Path
        Path to a grib2 file.
    """
    if wgrib2:
        p = subprocess.run(
            f"{wgrib2} -s {grib2filepath}",
            shell=True,
            capture_output=True,
            encoding="utf-8",
            check=True,
        )
        return p.stdout
    else:
        raise RuntimeError("wgrib2 command was not found.")


def create_index_files(path, overwrite=False):
    """Create an index file for all GRIB2 files in a directory.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to directory or file.
    overwrite : bool
        Overwrite index file if it exists.
    """
    path = Path(path).expand()
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
    fxx : int or pandas-parsable timedelta (e.g. "6H")
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
        date=None,
        *,
        valid_date=None,
        model=config["default"].get("model"),
        fxx=config["default"].get("fxx"),
        product=config["default"].get("product"),
        priority=config["default"].get("priority"),
        save_dir=config["default"].get("save_dir"),
        overwrite=config["default"].get("overwrite", False),
        verbose=config["default"].get("verbose", True),
        **kwargs,
    ):
        """Specify model output and find GRIB2 file at one of the sources."""
        self.fxx = fxx

        if isinstance(self.fxx, (str, pd.Timedelta)):
            # Convert pandas-parsable timedelta string to int in hours.
            self.fxx = pd.to_timedelta(fxx).round("1H").total_seconds() / 60 / 60
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

        if product is None:
            # The user didn't specify a product, so let's use the first
            # product in the model template.
            self.product = list(self.PRODUCTS)[0]
            log.info(f'`product` not specified. Will use "{self.product}".')
            # We need to rerun this so the sources have the new product value.
            getattr(model_templates, self.model).template(self)

        self.product_description = self.PRODUCTS[self.product]

        # Specify the suffix for the inventory index files.
        # Default value is `.grib2.idx`, but some have weird suffix,
        # like archived RAP on NCEI are `.grb2.inv`.
        self.IDX_SUFFIX = getattr(self, "IDX_SUFFIX", [".grib2.idx"])

        # Specify the index file type. By default, Herbie assumes the
        # index file was created with wgrib2.
        # But for ecmwf files with index files created with eccodes
        # the index files are in a different style.
        self.IDX_STYLE = getattr(self, "IDX_STYLE", "wgrib2")

        self.searchString_help = _searchString_help(self.IDX_STYLE)

        # Check the user input
        self._validate()

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

    def __repr__(self):
        """Representation in Notebook."""
        msg = (
            f"{ANSI.herbie} {self.model.upper()} model",
            f"{ANSI.italic}{self.product}{ANSI.reset} product initialized",
            f"{ANSI.green}{self.date:%Y-%b-%d %H:%M UTC}{ANSI.bright_green} F{self.fxx:02d}{ANSI.reset}",
            f"┊ {ANSI.orange}{ANSI.italic}source={self.grib_source}{ANSI.reset}",
        )
        return " ".join(msg)

    def __str__(self):
        """When Herbie class object is printed, print all properties."""
        # * Keep this simple so it runs fast.
        msg = (f"║HERBIE╠ {self.model.upper()}:{self.product}",)
        return " ".join(msg)

    def tell_me_everything(self):
        """Print all the attributes of the Herbie object."""
        msg = []
        for i in dir(self):
            if isinstance(getattr(self, i), (int, str, dict)):
                if not i.startswith("__"):
                    msg.append(f"self.{i}={getattr(self, i)}")
        msg = "\n".join(msg)
        print(msg)

    def __logo__(self):
        """For Fun, show the Herbie Logo."""
        print(ANSI.ascii)

    def _validate(self):
        """Validate the Herbie class input arguments."""
        # Accept model alias
        if self.model.lower() == "alaska":
            self.model = "hrrrak"

        _models = {m for m in dir(model_templates) if not m.startswith("__")}
        _products = set(self.PRODUCTS)

        assert self.date < datetime.utcnow(), "🔮 `date` cannot be in the future."
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
                expired = datetime.utcnow() - timedelta(days=14)
                expired = pd.to_datetime(f"{expired:%Y-%m-%d}")
                if self.date < expired:
                    self.priority.remove("nomads")

    def _ping_pando(self):
        """Pinging the Pando server before downloading can prevent a bad handshake."""
        try:
            requests.head("https://pando-rgw01.chpc.utah.edu/")
        except:
            print("🤝🏻⛔ Bad handshake with pando? Am I able to move on?")
            pass

    def _check_grib(self, url, min_content_length=10):
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

    def _check_idx(self, url, verbose=False):
        """Check if an index file exist for the GRIB2 URL."""
        # To check inventory files with slightly different URL structure
        # we will loop through the IDX_SUFFIX.

        if verbose:
            print(f"🐜 {self.IDX_SUFFIX=}")

        # Loop through IDX_SUFFIX options until we find one that exists
        for i in self.IDX_SUFFIX:
            if Path(url).suffix in {".grb", ".grib", ".grb2", ".grib2"}:
                idx_url = url.rsplit(".", maxsplit=1)[0] + i
            else:
                idx_url = url + i

            idx_exists = requests.head(idx_url).ok
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

    def find_grib(self):
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
            # NOTE: We will still get the idx files from a remote
            #       because they aren't stored locally, or are they?   # TODO: If the idx file is local, then use that

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
            grib_url = self.SOURCES[source]

            if source.startswith("local"):
                grib_path = Path(grib_url).expand()
                if grib_path.exists():
                    return [grib_path, source]
            elif self._check_grib(grib_url):
                return [grib_url, source]

        return [None, None]

    def find_idx(self):
        """Find an index file for the GRIB file."""
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
            grib_url = self.SOURCES[source]

            if source.startswith("local"):
                local_grib = Path(grib_url).expand()
                local_idx = local_grib.with_suffix(self.IDX_SUFFIX[0])
                if local_idx.exists():
                    return [local_idx, "local"]
            else:
                idx_exists, idx_url = self._check_idx(grib_url)

                if idx_exists:
                    return [idx_url, source]

        return [None, None]

    @property
    def get_remoteFileName(self, source=None):
        """Predict remote file name (assumes all sources are named the same)."""
        if source is None:
            source = list(self.SOURCES)[0]
        return self.SOURCES[source].split("/")[-1]

    @property
    def get_localFileName(self):
        """Predict the local file name."""
        return self.LOCALFILE

    def get_localFilePath(self, searchString=None):
        """Get full path to the local file."""

        # Predict the localFileName from the first model template SOURCE.
        localFilePath = (
            self.save_dir.expand()
            / self.model
            / f"{self.date:%Y%m%d}"
            / self.get_localFileName
        )

        # Check if any sources in a model template are "local"
        # (i.e., a custom template file)
        if any([i.startswith("local") for i in self.SOURCES.keys()]):
            localFilePath = next(
                (
                    Path(self.SOURCES[i]).expand()
                    for i in self.SOURCES
                    if i.startswith("local") and Path(self.SOURCES[i]).expand().exists()
                ),
                localFilePath,
            )

        if searchString is not None:
            # Reassign the index DataFrame with the requested searchString
            idx_df = self.inventory(searchString)

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

    @functools.cached_property
    def index_as_dataframe(self):
        """Read and cache the full index file."""

        if self.grib_source == "local" and wgrib2:
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
            df["valid_time"] = df["reference_time"] + pd.to_timedelta(f"{self.fxx}H")
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

            r = requests.get(self.idx)
            idxs = [json.loads(x) for x in r.text.split("\n") if x]
            r.close()
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
            df["step"] = pd.to_timedelta(df.step.astype(int), unit="H")
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
                    # ---- Used for searchString ------------------------------
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

    # TODO : Remove this in a future Herbie version
    def read_idx(self, searchString=None):
        warnings.warn(
            "The `read_idx` method has been renamed `inventory`.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.inventory(searchString=None)

    def inventory(self, searchString=None):
        """
        Inspect the GRIB2 file contents by reading the index file.

        This reads index files created with the wgrib2 utility.

        Parameters
        ----------
        searchString : str
            Filter dataframe by a searchString regular expression.
            Searches for strings in the index file lines, specifically
            the variable, level, and forecast_time columns.
            Execute ``_searchString_help()`` for examples of a good
            searchString.

            Read more in the user guide at
            https://herbie.readthedocs.io/en/latest/user_guide/searchString.html

        Returns
        -------
        A Pandas DataFrame of the index file.

        """
        df = self.index_as_dataframe

        # Filter DataFrame by searchString
        if searchString not in [None, ":"]:
            logic = df.search_this.str.contains(searchString)
            if logic.sum() == 0:
                print(
                    f"No GRIB messages found. There might be something wrong with {searchString=}"
                )
                print(_searchString_help(kind=self.IDX_STYLE))
            df = df.loc[logic]
        return df

    def download(
        self,
        searchString=None,
        *,
        source=None,
        save_dir=None,
        overwrite=None,
        verbose=None,
        errors="warn",
    ):
        """
        Download file from source.

        TODO: When we download a full file, the value of self.grib and
        TODO:   self.grib_source should change to represent the local file.

        Subsetting by variable follows the same principles described here:
        https://www.cpc.ncep.noaa.gov/products/wesley/fast_downloading_grib.html

        Parameters
        ----------
        searchString : str
            If None, download the full file. Else, use regex to subset
            the file by specific variables and levels.
            Read more in the user guide:
            https://herbie.readthedocs.io/en/latest/user_guide/searchString.html
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
            when searchString is not None because file subsets might
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

        def subset(searchString, outFile):
            """Download a subset specified by the regex searchString."""
            # TODO: Maybe optimize downloading multiple subsets with MultiThreading

            # TODO An alternative to downloadling subset with curl is
            # TODO  to use the request module directly.
            # TODO  >> headers = dict(Range=f"bytes={start_bytes}-{end_bytes}")
            # TODO  >> r = requests.get(grib_url, headers=headers)

            grib_source = self.grib
            if hasattr(grib_source, "as_posix") and grib_source.exists():
                # The GRIB source is local. Curl the local file
                # See https://stackoverflow.com/a/21023161/2383070
                grib_source = f"file://{str(self.grib)}"
            if verbose:
                print(
                    f'📇 Download subset: {self.__repr__()}{" ":60s}\n cURL from {grib_source}'
                )

            # -----------------------------------------------------
            # Download subsets of the file by byte range with cURL.
            #  Instead of using a single curl command for each row,
            #  group adjacent messages in the same curl command.

            # Find index groupings
            idx_df = self.inventory(searchString).copy()
            if verbose:
                print(
                    f"Found {ANSI.bold}{ANSI.green}{len(idx_df)}{ANSI.reset} grib messages."
                )
            idx_df["download_groups"] = idx_df.grib_message.diff().ne(1).cumsum()

            # cURL subsets of each group
            for i, curl_group in idx_df.groupby("download_groups"):
                if verbose:
                    print(f"Download subset group {i}")

                if verbose:
                    for _, row in curl_group.iterrows():
                        print(
                            f"  {row.grib_message:<3g} {ANSI.orange}{row.search_this}{ANSI.reset}"
                        )

                range = f"{curl_group.start_byte.min():.0f}-{curl_group.end_byte.max():.0f}".replace(
                    "nan", ""
                )

                if curl_group.end_byte.max() - curl_group.start_byte.min() < 0:
                    # The byte range for GRIB submessages (like in the
                    # RAP model's UGRD/VGRD) need to be handled differently.
                    # See https://github.com/blaylockbk/Herbie/issues/259
                    if verbose:
                        print(f"  ERROR: Invalid cURL range {range}; Skip message.")
                    continue

                if i == 1:
                    # If we are working on the first item, overwrite the existing file...
                    curl = f'''curl -s --range {range} "{grib_source}" > "{outFile}"'''
                else:
                    # ...all other messages are appended to the subset file.
                    curl = f'''curl -s --range {range} "{grib_source}" >> "{outFile}"'''

                if verbose:
                    print(curl)
                os.system(curl)

            if verbose:
                print(f"💾 Saved the subset to {outFile}")

        # This overrides the save_dir specified in __init__
        if save_dir is not None:
            self.save_dir = Path(save_dir).expand()

        if not hasattr(Path(self.save_dir).expand(), "exists"):
            self.save_dir = Path(self.save_dir).expand()

        # If the file exists in the localPath and we don't want to
        # overwrite, then we don't need to download it.
        outFile = self.get_localFilePath(searchString=searchString)

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

        if self.overwrite and self.grib_source.startswith("local"):
            # Search for the grib files on the remote archives again
            self.grib, self.grib_source = self.find_grib(overwrite=True)
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
        if self.idx is None and searchString is not None:
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
        if searchString in [None, ":"] or self.idx is None:
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
            subset(searchString, outFile)

        return outFile

    def xarray(
        self,
        searchString=None,
        backend_kwargs={},
        remove_grib=True,
        **download_kwargs,
    ):
        """
        Open GRIB2 data as xarray DataSet.

        Parameters
        ----------
        searchString : str
            Variables to read into xarray Dataset
        remove_grib : bool
            If True, grib file will be removed ONLY IF it didn't exist
            before we downloaded it.
        """
        download_kwargs = {**dict(overwrite=False), **download_kwargs}

        local_file = self.get_localFilePath(searchString=searchString)

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
        if searchString is None and remove_grib:
            warnings.warn(
                "Will not remove GRIB file because Herbie will only remove subsetted files (not full files)."
            )
            remove_grib = False
        #!==============================================================

        # Download file if local file does not exists
        if not local_file.exists() or download_kwargs["overwrite"]:
            self.download(searchString=searchString, **download_kwargs)

        # Backend kwargs for cfgrib
        backend_kwargs.setdefault("indexpath", "")
        backend_kwargs.setdefault(
            "read_keys", ["parameterName", "parameterUnits", "stepRange"]
        )
        backend_kwargs.setdefault("errors", "raise")

        # Use cfgrib.open_datasets, just in case there are multiple "hypercubes"
        # for what we requested.
        Hxr = cfgrib.open_datasets(
            local_file,
            backend_kwargs=backend_kwargs,
        )

        # Get CF grid projection information with pygrib and pyproj because
        # this is something cfgrib doesn't do (https://github.com/ecmwf/cfgrib/issues/251)
        # NOTE: Assumes the projection is the same for all variables
        with pygrib.open(str(local_file)) as grb:
            msg = grb.message(1)
            cf_params = CRS(msg.projparams).to_cf()

        # Funny stuff with polar stereographic (https://github.com/pyproj4/pyproj/issues/856)
        # TODO: Is there a better way to handle this? What about south pole?
        if cf_params["grid_mapping_name"] == "polar_stereographic":
            cf_params["latitude_of_projection_origin"] = cf_params.get(
                "latitude_of_projection_origin", 90
            )

        # Here I'm looping over each dataset in the list returned by cfgrib
        for ds in Hxr:
            # ----------------
            # Add some details
            # ----------------
            # Note: all attributes should still work with the `ds.to_netcdf()` method.
            ds.attrs["model"] = self.model
            ds.attrs["product"] = self.product
            ds.attrs["description"] = self.DESCRIPTION
            ds.attrs["remote_grib"] = self.grib
            ds.attrs["local_grib"] = str(local_file)
            ds.attrs["searchString"] = searchString

            # ----------------------
            # Attach CF grid mapping
            # ----------------------
            # http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#appendix-grid-mappings
            ds["gribfile_projection"] = None
            ds["gribfile_projection"].attrs = cf_params
            ds["gribfile_projection"].attrs[
                "long_name"
            ] = f"{self.model.upper()} model grid projection"

            # Assign this grid_mapping for all variables
            for var in list(ds):
                if var == "gribfile_projection":
                    continue
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
            except:
                if self.verbose:
                    print(
                        f"Note: Returning a list of [{len(Hxr)}] xarray.Datasets because cfgrib opened with multiple hypercubes."
                    )
            return Hxr

    # Shortcut Methods below
    def terrain(self, water_masked=True):
        """Return model terrain as an xarray.Dataset."""
        ds = self.xarray(":(?:HGT|LAND):surface")
        if water_masked:
            ds["orog"] = ds.orog.where(ds.lsm > 0)
        return ds
