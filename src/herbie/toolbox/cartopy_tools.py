"""
Cartopy Tools: Helpers to make quick Cartopy plots.

Does projection matter? YES!
(https://www.joaoleitao.com/different-world-map-projections/)

You've looked at maps with distortion that show Greenland the size of
South America. For the same reason, you should show data on appropriate
projection globes. Projection may better help you interpret results.

For global plots, consider using Mollweide projection
over Mercator or Robinson. From the website above,

    [Mollweide] sacrifices the precision of some of the angles and
    shapes, in exchange for a better representation of the planet's
    proportions when that is an important consideration.

    [Robinson] represented the continents more accurately than the
    Mercator Projection, the poles are highly distorted.

The Winkel Tripel Projection may also be more appropriate than Robinson,
but is not yet supported by Cartopy.
"""

import urllib.request

import cartopy.crs as ccrs
import cartopy.feature as feature
import cartopy.io.img_tiles as cimgt
import matplotlib.pyplot as plt
import numpy as np
import requests
import shapely.geometry as sgeom
import xarray as xr
from cartopy.io import shapereader
from metpy.plots import USCOUNTIES

from typing import Literal, Optional, Union
from herbie import Path

try:
    import geopandas
except Exception:
    # warnings.warn(
    #    f'{e} Without geopandas, you cannot subset some NaturalEarthFeatures shapefiles, like "Major Highways" from roads.'
    # )
    pass

ExtentPadding = Union[Literal["auto"], float, dict[str, float]]

pc = ccrs.PlateCarree()
pc._threshold = 0.01  # https://github.com/SciTools/cartopy/issues/8


def to_180(lon):
    """
    Wrap longitude from degrees [0, 360] to degrees [-180, 180].

    Parameters
    ----------
    lon : array_like
        Longitude values
    """
    lon = (lon + 180) % 360 - 180
    return lon


def to_360(lon):
    """
    Wrap longitude from degrees [-180, 180] to degrees [0, 360].

    Parameters
    ----------
    lon : array_like
        Longitude values
    """
    lon = (lon - 360) % 360
    return lon


# Map extent regions.
_extents = dict(
    NW=(-180, 0, 0, 90),
    SW=(-180, 0, -90, 0),
    NE=(0, 180, 0, 90),
    SE=(0, 180, -90, 0),
    CONUS=(-130, -60, 20, 55),
)


########################################################################
# Methods attached to axes created by `EasyMap`
def _adjust_extent(
    self,
    pad: ExtentPadding = "auto",
    fraction: float = 0.05,
    verbose: bool = False,
):
    """
    Adjust the extent of an existing cartopy axes.

    This is useful to fine-tune the extent of a map after the extent
    was automatically made by a cartopy plotting method.

    Parameters
    ----------
    pad : float or dict
        If float, pad the map the same on all sides. Default is half a degree.
        If dict, specify pad on each side.
            - 'top' - padding north of center point
            - 'bottom'- padding south of center point
            - 'left' - padding east of center point
            - 'right' - padding west of center point
            - 'default' - padding when pad is unspecified
        Example: ``pad=dict(top=.5, default=.2)`` is the same as
                 ``pad=dict(top=.5, bottom=.2, left=.2, right=.2)``
        Note: Use negative numbers to remove padding.
    fraction : float
        When pad is 'auto', adjust the sides by a set fraction.
        The default 0.05 will give 5% padding on each side.
    """
    # Can't shrink the map extent by more than half in each direction, duh.
    assert fraction > -0.5, "Fraction must be larger than -0.5."

    crs = self.projection

    west, east, south, north = self.get_extent(crs=crs)

    if pad == "auto":
        pad = {}

    if isinstance(pad, dict):
        xmin, xmax = self.get_xlim()
        default_pad = (xmax - xmin) * fraction
        pad.setdefault("default", default_pad)
        for i in ["top", "bottom", "left", "right"]:
            pad.setdefault(i, pad["default"])
    else:
        pad = dict(top=pad, bottom=pad, left=pad, right=pad)

    ymin, ymax = crs.y_limits
    north = np.minimum(ymax, north + pad["top"])
    south = np.maximum(ymin, south - pad["bottom"])
    east = east + pad["right"]
    west = west - pad["left"]

    self.set_extent([west, east, south, north], crs=crs)

    if verbose:
        print(f"📐 Adjust Padding for {crs.__class__}: {pad}")

    return self.get_extent(crs=crs)


def _center_extent(
    self,
    lon: Optional[Union[int, float]] = None,
    lat: Optional[Union[int, float]] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    *,
    pad: ExtentPadding = "auto",
    verbose: bool = False,
):
    """
    Change the map extent to be centered on a point and adjust padding.

    Parameters
    ----------
    lon, lat : float or None
        Latitude and Longitude of the center point **in degrees**.
        If None, must give argument for ``city``.
    city : str or None
        If string, center over city location.
    pad : float or dict
        Default is 'auto', which defaults to ~5 degree padding on each side.
        If float, pad the map the same on all sides (in crs units).
        If dict, specify pad on each side (in crs units).
            - 'top' - padding north of center point
            - 'bottom'- padding south of center point
            - 'left' - padding east of center point
            - 'right' - padding west of center point
            - 'default' - padding when pad is unspecified (default is 5)
        Example: ``pad=dict(top=5, default=10)`` is the same as
                 ``pad=dict(top=5, bottom=10, left=10, right=10)``
    """
    crs = self.projection

    if city is not None:
        places = shapereader.natural_earth("10m", "cultural", "populated_places")
        df = geopandas.read_file(places)
        point = df[df.NAME == city]
        assert len(point) > 0, f"🏙 Sorry, the city '{city}' was not found."
        lat = point.LATITUDE.item()
        lon = point.LONGITUDE.item()
    elif state is not None:
        state_center = state_polygon(state).centroid
        lon = state_center.x
        lat = state_center.y

    # Convert input lat/lon in degrees to the crs units
    lon, lat = crs.transform_point(lon, lat, src_crs=pc)

    if pad == "auto":
        pad = dict()

    if isinstance(pad, dict):
        # This default gives 5 degrees padding on each side
        # for a PlateCarree projection. Pad is similar for other
        # projections but not exactly 5 degrees.
        xmin, xmax = crs.x_limits
        default_pad = (xmax - xmin) / 72  # Because 360/72 = 5 degrees
        pad.setdefault("default", default_pad)
        for i in ["top", "bottom", "left", "right"]:
            pad.setdefault(i, pad["default"])
    else:
        pad = dict(top=pad, bottom=pad, left=pad, right=pad)

    ymin, ymax = crs.y_limits
    north = np.minimum(ymax, lat + pad["top"])
    south = np.maximum(ymin, lat - pad["bottom"])
    east = lon + pad["right"]
    west = lon - pad["left"]

    self.set_extent([west, east, south, north], crs=crs)

    if verbose:
        print(f"📐 Padding from point for {crs.__class__}: {pad}")

    return self.get_extent(crs=crs)


def _copy_extent(self, src_ax):
    """
    Copy the extent from an axes.

    .. note::
        Copying extent from different projections might not result in
        what you expect.

    Parameters
    ----------
    src_ax : cartopy axes
        A source cartopy axes to copy extent from onto the existing axes.

    Examples
    --------
    >>> # Copy extent of ax2 to ax1
    >>> ax1.copy_extent(ax2)

    """
    src_ax = check_cartopy_axes(src_ax)

    self.set_extent(src_ax.get_extent(crs=pc), crs=pc)

    return self.get_extent(crs=pc)


########################################################################
# Main Functions
def check_cartopy_axes(
    ax=None, crs=pc, *, fignum: Optional[int] = None, verbose: bool = False
):
    """
    Check if an axes is a cartopy axes, else create a new cartopy axes.

    Parameters
    ----------
    ax : {None, cartopy.mpl.geoaxes.GeoAxesSubplot}
        If None and plt.gca() is a cartopy axes, then use current axes.
        Else, create a new cartopy axes with specified crs.
    crs : cartopy.crs
        If the axes being checked is not a cartopy axes, then create one
        with this coordinate reference system (crs, aka "projection").
        Default is ccrs.PlateCarree()
    fignum : int
        If given, create a new figure and supblot for the given crs.
        (This might be handy in a loop when you want to create maps on
        several figures instead of plotting on the same figure.)
    """
    if isinstance(fignum, int):
        plt.figure(fignum)
        ax = plt.subplot(1, 1, 1, projection=crs)
        return ax

    # A cartopy axes should be of type `cartopy.mpl.geoaxes.GeoAxesSubplot`
    # One way to check that is to see if ax has the 'coastlines' attribute.
    if ax is None:
        if hasattr(plt.gca(), "coastlines"):
            if verbose:
                print("🌎 Using the current cartopy axes.")
            return plt.gca()
        else:
            if verbose:
                print(
                    f"🌎 The current axes is not a cartopy axes. Will create a new cartopy axes with crs={crs.__class__}."
                )
            # Close the axes we just opened in our test
            plt.close()
            # Create a new cartopy axes
            return plt.axes(projection=crs)
    else:
        if hasattr(ax, "coastlines"):
            if verbose:
                print("🌎 Thanks! It appears the axes you provided is a cartopy axes.")
            return ax
        else:
            raise TypeError("🌎 Sorry. The `ax` you gave me is not a cartopy axes.")


def get_ETOPO1(
    top: Literal["bedrock", "ice"] = "ice",
    coarsen: Optional[int] = None,
    thin: Optional[int] = None,
):
    """
    Return the ETOPO1 elevation and bathymetry DataArray.

    The ETOPO1 dataset is huge (446 MB). This function saves coarsened
    versions of the data for faster loading.

    Download the data from http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NGDC

    An alternatvie source is https://ngdc.noaa.gov/mgg/global/, but the
    Dataset may have a different structure.


    Parameters
    ----------
    top : {'bedrock', 'ice'}
        There are two types of ETOPO1 files, one that is the top of the
        ice layers, and another that is the top of the bedrock. This
        is necessary for Greenland and Antarctic ice sheets. I'm guessing
        that 99% of the time you will want the top of the ice sheets.
    thin : int
        Thin the Dataset by getting every nth element
    coarsen : int
        Coarsen the Dataset by taking the mean of the nxn box.
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
        print(
            f"\r🚛💨  Download ETOPO1 {top} Progress: {chunk_progress:.2f}% of {total_size_MB:.1f} MB\r",
            end="",
        )

    if coarsen == 1:
        coarsen = None
    if thin == 1:
        thin = None
    assert not all([coarsen, thin]), "Both `coarsen` and `thin` cannot be None."

    # If the ETOPO1 data does not exists, then download it.
    # The coarsen method is slow, so save a copy to load.
    # The thin method is fast, so don't worry about saving a copy.
    src = f"http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NGDC/.ETOPO1/.z_{top}/data.nc"
    dst = Path(f"$HOME/.local/share/ETOPO1/ETOPO1_{top}.nc").expand()
    dst_coarsen = Path(
        f"$HOME/.local/share/ETOPO1/ETOPO1_{top}_coarsen-{coarsen}.nc"
    ).expand()

    if not dst.exists():
        # Download the full ETOPO1 dataset
        if not dst.parent.exists():
            dst.parent.mkdir(parents=True)
        urllib.request.urlretrieve(src, dst, _reporthook)
        print(f"{' ':70}", end="")

    if coarsen:
        if dst_coarsen.exists():
            ds = xr.open_dataset(dst_coarsen)
        else:
            ds = xr.open_dataset(dst)
            ds = ds.coarsen({"lon": coarsen, "lat": coarsen}, boundary="pad").mean()
            ds.to_netcdf(dst_coarsen)
    else:
        ds = xr.open_dataset(dst)
        if thin:
            ds = ds.thin(thin)

    return ds[f"z_{top}"]


def inset_global_map(
    ax,
    x: float = 0.95,
    y: float = 0.95,
    size: float = 0.3,
    theme: Optional[Literal["dark", "grey"]] = None,
    facecolor: str = "#f88d0083",
    kind: Literal["point", "area"] = "area",
):
    """Add an inset map showing the location of the main map on the globe.

    This was pieced together from these resources
    - https://predictablysunny.com/posts/inset_map_cartopy/
    - https://scitools.org.uk/cartopy/docs/latest/gallery/lines_and_polygons/effects_of_the_ellipse.html#sphx-glr-gallery-lines-and-polygons-effects-of-the-ellipse-py
    - https://stackoverflow.com/a/53712048/2383070

    Parameters
    ----------
    ax : a cartopy axes
        A cartopy axes with the extent already set (not global).
    kind : {'point', 'area'}
        If 'area', display the area of the data on the global map.
        If 'point', display the center point of the map extent.
    """
    # ======================
    # Find the extent center
    extent = ax.get_extent(crs=pc)
    center_lon = (extent[0] + extent[1]) / 2
    center_lat = (extent[2] + extent[3]) / 2

    # ====================
    # Create the Inset Map

    # Location and size of inset on axis
    inset_x = x
    inset_y = y
    inset_size = size

    # Create and position inset
    ortho = ccrs.Orthographic(central_latitude=center_lat, central_longitude=center_lon)
    ax_inset = ax.inset_axes(
        [inset_x - inset_size / 2, inset_y - inset_size / 2, inset_size, inset_size],
        projection=ortho,
    )
    ax_inset.set_global()
    ax_inset.set_zorder(1000000)  # make sure the inset is on top of everything

    # ===================
    # Inset Map Cosmetics
    EasyMap(ax=ax_inset, theme=theme, linewidth=0).STATES().LAND().OCEAN()

    ax_inset.gridlines(
        xlocs=range(-180, 180, 10),
        ylocs=range(-90, 91, 10),
        lw=0.1,
        alpha=0.2,
    )

    if kind == "point":
        ax_inset.scatter(center_lon, center_lat, facecolor=facecolor, transform=pc)

    elif kind == "area":
        # =========================
        # Add Bounding Box to Inset

        # Create Boundary box: need to increase the boundary of box Polygon coords
        crs_extent = ax.get_extent(crs=ax.projection)
        ring = sgeom.box(
            crs_extent[0], crs_extent[2], crs_extent[1], crs_extent[3]
        ).exterior

        # Set the number of points along a side
        n_points = 200

        # Create a new LinearRing with additional points
        new_ring_coords = []
        for i in range(len(ring.coords) - 1):
            start = ring.coords[i]
            end = ring.coords[i + 1]
            line = sgeom.LineString([start, end])
            new_points = [
                line.interpolate(i) for i in np.linspace(1, line.length, n_points)
            ]
            new_ring_coords += [start] + new_points + [end]
        new_ring = sgeom.LinearRing(new_ring_coords)

        # Add bounding box to map
        ax_inset.add_geometries(
            [new_ring],
            crs=ax.projection,
            facecolor=facecolor,
        )
    else:
        raise ValueError("`kind` must be either 'point' or 'area'.")

    return ax_inset


def state_polygon(
    state: Optional[str] = None,
    country: str = "USA",
    county: Optional[str] = None,
    verbose: bool = True,
):
    """
    Return a shapely polygon of US state boundaries or country borders.

    GeoJSON Data: https://raw.githubusercontent.com/johan/world.geo.json
    Helpful tip: https://medium.com/@pramukta/recipe-importing-geojson-into-shapely-da1edf79f41d

    Parameters
    ----------
    state : str
        Abbreviated state {'UT', 'CA', 'ID', etc.}
    country : str
        Abbreviated country {'USA', 'CAN', 'MEX', 'DEU', 'FRA', 'CHN', 'RUS', etc.}
    county : str
        Abbreviated county (for US states only)
    """
    if country == "USA":
        if county is None:
            URL = f"https://raw.githubusercontent.com/johan/world.geo.json/master/countries/USA/{state.upper()}.geo.json"
        else:
            URL = f"https://raw.githubusercontent.com/johan/world.geo.json/master/countries/USA/{state.upper()}/{county}.geo.json"
    else:
        URL = f"https://raw.githubusercontent.com/johan/world.geo.json/master/countries/{country.upper()}.geo.json"

    f = requests.get(URL)

    features = f.json()["features"]
    poly = sgeom.GeometryCollection(
        [sgeom.shape(feature["geometry"]).buffer(0) for feature in features]
    )

    if verbose:
        print(
            "Here's the Polygon; you may need to do `_.geoms[i]` to get Polygons from the shape."
        )

    return poly


class EasyMap:
    """
    Build a Cartopy axes with commonly used map elements.

    Most the time when I use Cartopy, I just want to make a map that I
    can easily add data to. This class does about 98% of what I need
    from Cartopy.
    """

    def __init__(
        self,
        scale: Literal["110m", "50m", "10m"] = "110m",
        ax=None,
        crs=pc,
        *,
        figsize=None,
        fignum: int = None,
        dpi: int = None,
        theme: Optional[Literal["dark", "grey"]] = None,
        add_coastlines: bool = True,
        facecolor: Optional[str] = None,
        coastlines_kw={},
        verbose: bool = False,
        **kwargs,
    ):
        """
        Initialize a Cartopy axes.

        Coastlines are added automatically. Use other methods to add
        other common features to the Cartopy axes.

        Extra Methods
        -------------
        .adjust_extent
        .center_extent
        .copy_extent

        Parameters
        ----------
        scale : {'10m', '50m' 110m'}
            The cartopy feature's level of detail.
            .. note::  The ``'10m'`` scale for OCEAN and LAND takes a *long* time.
        ax : plot axes
            The axis to add the feature to.
            If None, it will create a new cartopy axes with ``crs``.
        crs : cartopy.crs
            Coordinate reference system (aka "projection") to create new map
            if no cartopy axes is given. Default is ccrs.PlateCarree.
        theme : {None, 'dark', 'grey', 'gray'}
            Use alternative color themes for land and water.

            .. figure:: _static/BB_maps/common_features-1.png
            .. figure:: _static/BB_maps/common_features-2.png

        add_coastlines : bool
            For convince, the coastlines are added to the axes by default.
            This can be turned off and instead controlled with the COASTLINES
            method.
        coastlines_kw : dict
            kwargs for the default COASTLINES method.

        figsize : tuple or float
            Set the figure size.
            If single number given, then will make a square figure.
        fignum : int
            If given, create a new figure and supblot for the given crs.
            (This might be handy in a loop when you want to create maps on
            several figures instead of plotting on the same figure.)
        dpi : int
            Set the figure dpi

        Examples
        --------
        https://github.com/blaylockbk/Carpenter_Workshop/blob/main/notebooks/demo_cartopy_tools.ipynb

        >>> feat = EasyMap()
        >>> feat.OCEAN().STATES()
        >>> ax = feat.ax

        Alternatively,

        >>> ax = EasyMap().ax
        >>> feat = ax.EasyMap
        >>> feat.OCEAN().STATES()
        """
        self.scale = scale
        self.ax = ax
        self.crs = crs
        self.figsize = figsize
        self.fignum = fignum
        self.dpi = dpi
        self.theme = None if theme is None else theme.lower()
        self.verbose = verbose
        self.kwargs = kwargs

        self.ax = check_cartopy_axes(
            ax=self.ax, crs=self.crs, fignum=self.fignum, verbose=self.verbose
        )

        # In a round-about way, you can get this EasyMap object from the axes
        # >>> ax = EasyMap().ax
        # >>> ax.EasyMap.STATES()
        self.ax.EasyMap = self

        self.kwargs.setdefault("linewidth", 0.75)

        # NOTE: I don't use the 'setdefault' method here because it doesn't
        # work as expect when switching between themes.
        if self.theme == "dark":
            self.land = "#060613"  # dark (default)
            self.land1 = "#3f3f3f"  # lighter (alternative)
            self.water = "#0f2b38"
            self.ax.set_facecolor(self.land)
            self.kwargs = {**{"edgecolor": ".5"}, **self.kwargs}
        elif self.theme in {"grey", "gray"}:
            self.land = "#bdbdbd"  # dark (default)
            self.land1 = "#bdbdbd"  # lighter (alternative)
            self.water = "#ffffff"
            self.ax.set_facecolor(self.land)
            self.kwargs = {**{"edgecolor": ".5"}, **self.kwargs}
        else:
            self.land = "#efefdb"  # tan (default)
            self.land1 = "#dbdbdb"  # grey (alternative)
            self.water = "#97b6e1"
            self.kwargs = {**{"edgecolor": ".15"}, **self.kwargs}

        if facecolor:
            # Instead of applying both LAND and OCEAN,
            # it may be faster to just set the facecolor of land
            # and then only apply the OCEAN method.
            if facecolor.lower() == "land":
                self.ax.set_facecolor(self.land)
            elif facecolor.lower() == "land1":
                self.ax.set_facecolor(self.land1)
            elif facecolor.lower() == "water":
                self.ax.set_facecolor(self.water)
            else:
                self.ax.set_facecolor(facecolor)

        if add_coastlines:
            # Default map will automatically add COASTLINES
            self.COASTLINES(**coastlines_kw)

        if figsize is not None:
            if hasattr(figsize, "__len__"):
                plt.gcf().set_figwidth(self.figsize[0])
                plt.gcf().set_figheight(self.figsize[1])
            else:
                plt.gcf().set_figwidth(self.figsize)
                plt.gcf().set_figheight(self.figsize)
        if dpi is not None:
            plt.gcf().set_dpi(self.dpi)

        # Attach my custom methods
        self.ax.__class__.adjust_extent = _adjust_extent
        self.ax.__class__.center_extent = _center_extent
        self.ax.__class__.copy_extent = _copy_extent

    # ========================
    # Commonly needed features
    def COASTLINES(self, **kwargs):
        """Add coastlines to map."""
        kwargs.setdefault("zorder", 100)
        kwargs.setdefault("facecolor", "none")
        kwargs = {**self.kwargs, **kwargs}
        self.ax.add_feature(feature.COASTLINE.with_scale(self.scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 COASTLINES:", kwargs)
        return self

    def BORDERS(self, **kwargs):
        """Add country borders to map (ecludes coastlines)."""
        kwargs.setdefault("linewidth", 0.5)
        kwargs = {**self.kwargs, **kwargs}
        self.ax.add_feature(feature.BORDERS.with_scale(self.scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 BORDERS:", kwargs)
        return self

    def STATES(self, **kwargs):
        """State and Province borders.

        Note: If scale="110m", only the US States are drawn.
              If scale="50m", then more country states/provinces are drawn.
              If scale="10m", then even *more* countries drawn.
        """
        kwargs.setdefault("alpha", 0.15)

        kwargs = {**self.kwargs, **kwargs}
        self.ax.add_feature(feature.STATES.with_scale(self.scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 STATES:", kwargs)
        return self

    def STATES2(self, **kwargs):
        """States and Provinces (US, Canada, Australia, Brazil, China, Inda, etc.).

        Alternative source for data than provided by STATES.
        """
        kwargs.setdefault("alpha", 0.15)

        kwargs = {**self.kwargs, **kwargs}
        states_provinces = feature.NaturalEarthFeature(
            category="cultural",
            name="admin_1_states_provinces_lines",
            scale="50m",
            facecolor="none",
        )
        self.ax.add_feature(states_provinces, **kwargs)

        if self.verbose == "debug":
            print("🐛 STATES2:", kwargs)
        return self

    def COUNTIES(self, counties_scale="20m", **kwargs):
        """Add US counties to map."""
        _counties_scale = {"20m", "5m", "500k"}
        assert (
            counties_scale in _counties_scale
        ), f"counties_scale must be {_counties_scale}"
        kwargs.setdefault("linewidth", 0.33)
        kwargs.setdefault("alpha", 0.15)
        kwargs = {**self.kwargs, **kwargs}
        self.ax.add_feature(USCOUNTIES.with_scale(counties_scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 COUNTIES:", kwargs)
        return self

    def OCEAN(self, **kwargs):
        """Add color-filled ocean area to map."""
        kwargs.setdefault("edgecolor", "none")
        kwargs = {**self.kwargs, **kwargs}

        if self.theme is not None:
            kwargs = {**{"facecolor": self.water}, **kwargs}

        self.ax.add_feature(feature.OCEAN.with_scale(self.scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 OCEAN:", kwargs)
        return self

    def LAND(self, **kwargs):
        """Add color-filled land area to map."""
        kwargs.setdefault("edgecolor", "none")
        kwargs.setdefault("linewidth", 0)
        kwargs = {**self.kwargs, **kwargs}

        if self.theme is not None:
            kwargs = {**{"facecolor": self.land}, **kwargs}

        self.ax.add_feature(feature.LAND.with_scale(self.scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 LAND:", kwargs)
        return self

    def RIVERS(self, **kwargs):
        """Add rivers to map."""
        kwargs.setdefault("linewidth", 0.3)
        kwargs = {**self.kwargs, **kwargs}
        kwargs = {**{"color": self.water}, **kwargs}

        self.ax.add_feature(feature.RIVERS.with_scale(self.scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 RIVERS:", kwargs)
        return self

    def LAKES(self, **kwargs):
        """Add color-filled lake area to map."""
        kwargs.setdefault("linewidth", 0)
        kwargs = {**self.kwargs, **kwargs}

        if self.theme is not None:
            kwargs = {**{"facecolor": self.water}, **kwargs}
            kwargs = {**{"edgecolor": self.water}, **kwargs}
        else:
            kwargs = {**{"facecolor": feature.COLORS["water"]}, **kwargs}
            kwargs = {**{"edgecolor": feature.COLORS["water"]}, **kwargs}

        self.ax.add_feature(feature.LAKES.with_scale(self.scale), **kwargs)
        if self.verbose == "debug":
            print("🐛 LAKES:", kwargs)
        return self

    # =============================
    # Less commonly needed features
    def TERRAIN(
        self,
        coarsen: int = 30,
        *,
        top: Literal["ice", "bedrock"] = "ice",
        kind: Literal["pcolormesh", "contourf"] = "pcolormesh",
        extent=None,
        **kwargs,
    ):
        """
        Add terrain data from ETOPO1 dataset to map.

        Parameters
        ----------
        coarsen : int
            ETOPO1 data is a 1-minute arc dataset. This is huge.
            For global plots, you don't need this resolution, and can
            be happy with a 30-minute arc resolution (default).
        top : {"ice", "bedrock"}
            Top of the elevation model. "ice" is top of ice sheets in
            Greenland and Antarctica and "bedrock" is elevation of
            of ground under the ice.
        kind : {"contourf", "pcolormesh"}
            Plot data as a contour plot or pcolormesh
        extent :
            Trim the huge dataset to a specific region. (Variable cases).
            - by hemisphere {"NE", "SE", "NW", "SW"}
            - by region {"CONUS"}
            - by extent (len==4 tuple/list), e.g. `[-130, -100, 20, 50]`
            - by xarray.Dataset (must have coordinates 'lat' and 'lon')
              TODO: Currently does not allow domains that cross -180 lon.
        """
        da = get_ETOPO1(top=top, coarsen=coarsen)

        if extent:
            if isinstance(extent, (list, tuple)):
                assert (
                    len(extent) == 4
                ), "extent tuple must be len 4 (minLon, maxLon, minLat, maxLat)"
            elif isinstance(extent, str):
                assert (
                    extent in _extents
                ), f"extent string must be one of {_extents.keys()}"
                extent = _extents[extent]
            elif hasattr(extent, "coords"):
                # Get extent from lat/lon bounds in xarray DataSet
                extent = extent.rename({"latitude": "lat", "longitude": "lon"})
                extent["lon"] = to_180(extent["lon"])
                extent = (
                    extent.lon.min().item(),
                    extent.lon.max().item(),
                    extent.lat.min().item(),
                    extent.lat.max().item(),
                )

            da = da.where(
                (da.lon >= extent[0])
                & (da.lon <= extent[1])
                & (da.lat >= extent[2])
                & (da.lat <= extent[3])
            )

        # Get "land" points (elevation is 0 and above, crude estimation)
        da = da.where(da >= 0)

        kwargs.setdefault("zorder", 0)
        kwargs.setdefault("cmap", "YlOrBr")
        kwargs.setdefault("levels", range(0, 8000, 500))
        kwargs.setdefault("vmin", 0)
        kwargs.setdefault("vmax", 8000)

        if kind == "contourf":
            _ = kwargs.pop("vmax")
            _ = kwargs.pop("vmin")
            self.ax.contourf(da.lon, da.lat, da, transform=pc, **kwargs)
        elif kind == "pcolormesh":
            _ = kwargs.pop("levels")
            self.ax.pcolormesh(da.lon, da.lat, da, transform=pc, **kwargs)

        return self

    def BATHYMETRY(
        self,
        coarsen: int = 30,
        *,
        top: Literal["ice", "bedrock"] = "ice",
        kind: Literal["pcolormesh", "contourf"] = "pcolormesh",
        extent=None,
        **kwargs,
    ):
        """
        Add bathymetry data from ETOPO1 dataset to map.

        Parameters
        ----------
        coarsen : int
            ETOPO1 data is a 1-minute arc dataset. This is huge.
            For global plots, you don't need this resolution, and can
            be happy with a 30-minute arc resolution (default).
        top : {"ice", "bedrock"}
            Top of the elevation model. "ice" is top of ice sheets in
            Greenland and Antarctica and "bedrock" is elevation of
            of ground under the ice.
        kind : {"contourf", "pcolormesh"}
            Plot data as a contour plot or pcolormesh
        extent :
            Trim the huge dataset to a specific region. (Variable cases).
            - by hemisphere {"NE", "SE", "NW", "SW"}
            - by region {"CONUS"}
            - by extent (len==4 tuple/list), e.g. `[-130, -100, 20, 50]`
            - by xarray.Dataset (must have coordinates 'lat' and 'lon')
              TODO: Currently does not allow domains that cross -180 lon.
        """
        da = get_ETOPO1(top=top, coarsen=coarsen)

        if extent:
            if isinstance(extent, (list, tuple)):
                assert (
                    len(extent) == 4
                ), "extent tuple must be len 4 (minLon, maxLon, minLat, maxLat)"
            elif isinstance(extent, str):
                assert (
                    extent in _extents
                ), f"extent string must be one of {_extents.keys()}"
                extent = _extents[extent]
            elif hasattr(extent, "coords"):
                # Get extent from lat/lon bounds in xarray DataSet
                extent = extent.rename({"latitude": "lat", "longitude": "lon"})
                extent["lon"] = to_180(extent["lon"])
                extent = (
                    extent.lon.min().item(),
                    extent.lon.max().item(),
                    extent.lat.min().item(),
                    extent.lat.max().item(),
                )

            da = da.where(
                (da.lon >= extent[0])
                & (da.lon <= extent[1])
                & (da.lat >= extent[2])
                & (da.lat <= extent[3])
            )

        # Get "water" points (elevation is 0 and above, crude estimation)
        da = da.where(da <= 0)

        kwargs.setdefault("zorder", 0)
        kwargs.setdefault("cmap", "Blues_r")
        kwargs.setdefault("levels", range(-10000, 1, 500))
        kwargs.setdefault("vmax", 0)
        kwargs.setdefault("vmin", -10000)

        if kind == "contourf":
            _ = kwargs.pop("vmax")
            _ = kwargs.pop("vmin")
            self.ax.contourf(da.lon, da.lat, da, transform=pc, **kwargs)
        elif kind == "pcolormesh":
            _ = kwargs.pop("levels")
            self.ax.pcolormesh(da.lon, da.lat, da, transform=pc, **kwargs)

        return self

    def PLAYAS(self, **kwargs):
        """Add color-filled playa area to map."""
        kwargs.setdefault("linewidth", 0)
        kwargs = {**self.kwargs, **kwargs}

        if self.theme == "dark":
            kwargs = {**{"facecolor": "#4D311A73"}, **kwargs}
            kwargs = {**{"edgecolor": "none"}, **kwargs}
        elif self.theme in {"grey", "gray"}:
            kwargs = {**{"facecolor": "#42424273"}, **kwargs}
            kwargs = {**{"edgecolor": "none"}, **kwargs}
        else:
            kwargs = {**{"facecolor": "#FDA65473"}, **kwargs}
            kwargs = {**{"edgecolor": "none"}, **kwargs}

        playa = feature.NaturalEarthFeature("physical", "playas", "10m")
        self.ax.add_feature(playa, **kwargs)
        if self.verbose == "debug":
            print("🐛 PLAYAS:", kwargs)
        return self

    def TIMEZONE(self, **kwargs):
        """Add timezone boundaries to map."""
        kwargs.setdefault("linewidth", 0.2)
        kwargs.setdefault("facecolor", "none")
        kwargs.setdefault("linestyle", ":")
        kwargs = {**self.kwargs, **kwargs}
        tz = feature.NaturalEarthFeature("cultural", "time_zones", "10m")
        self.ax.add_feature(tz, **kwargs)
        if self.verbose == "debug":
            print("🐛 TIMEZONE:", kwargs)
        return self

    def ROADS(self, road_types=None, **kwargs):
        """
        Add major roads to map.

        Parameters
        ----------
        road_types : None, str, list
            Filter the types of roads you want. The road type may be a single
            string or a list of road types.
            e.g. ['Major Highway', 'Secondary Highway']

        Of course, the shapefile has many other road classifiers for each
        road, like "level" (Federal, State, Interstate), road "name",
        "length_km", etc. Filters for each of these could be added if I
        need them later.
        """
        kwargs.setdefault("edgecolor", "#b30000")
        kwargs.setdefault("facecolor", "none")
        kwargs.setdefault("linewidth", 0.2)

        kwargs = {**self.kwargs, **kwargs}

        if road_types is None:
            # Plot all roadways
            roads = feature.NaturalEarthFeature("cultural", "roads", "10m", **kwargs)
            self.ax.add_feature(roads)
        else:
            # Specify the type of road to include in plot
            if isinstance(road_types, str):
                road_types = [road_types]
            shpfilename = shapereader.natural_earth("10m", "cultural", "roads")
            df = geopandas.read_file(shpfilename)
            _types = df["type"].unique()
            assert np.all(
                [i in _types for i in road_types]
            ), f"`ROADS_kwargs['type']` must be a list of these: {_types}"
            road_geom = df.loc[
                df["type"].apply(lambda x: x in road_types)
            ].geometry.values
            self.ax.add_geometries(road_geom, crs=pc, **kwargs)

        if self.verbose == "debug":
            print("🐛 ROADS:", kwargs)
        return self

    def PLACES(
        self,
        country: str = "United States",
        rank: int = 2,
        scatter: bool = True,
        labels: bool = True,
        label_kw={},
        scatter_kw={},
    ):
        """
        Add points and labels for major cities to map.

        Parameters
        ----------
        country : str
            Country to filter
        rank : int
            City rank threshold. Large cities have small rank. Small
            cities have large rank.
        scatter : bool
            Add scatter points
        labels : bool
            Add city name labels
        """
        scatter_kw.setdefault("marker", ".")
        label_kw.setdefault("fontweight", "bold")
        label_kw.setdefault("alpha", 0.5)

        places = shapereader.natural_earth("10m", "cultural", "populated_places")
        df = geopandas.read_file(places)

        df = df[df.SOV0NAME == country]
        df = df[df.SCALERANK <= rank]

        xs = df.geometry.values.x
        ys = df.geometry.values.y
        names = df.NAME

        if scatter:
            self.ax.scatter(xs, ys, transform=pc, **scatter_kw)

        if labels:
            for x, y, name in zip(xs, ys, names):
                self.ax.text(x, y, name, clip_on=True, **label_kw)
        return self

    # ============
    # Tiled images
    def STAMEN(
        self,
        style: Literal[
            "terrain-background", "terrain", "toner-background", "toner", "watercolor"
        ] = "terrain-background",
        zoom: int = 3,
        alpha=1,
    ):
        """
        Add Stamen map tiles to background.

        When adding a tile product to a map, it might be better to add
        it to the map first, then set the map extent, then make a separate
        call to ``EasyMap()`` to add other features like roads and
        counties. The reason is because, if you add a tile map to

        Parameters
        ----------
        style : {'terrain-background', 'terrain', 'toner-background', 'toner', 'watercolor'}
            Type of image tile
        zoom : int
            Zoom level between 0 and 10.
        alpha : float
            Alpha value (transparency); a value between 0 and 1.
        """
        # Zoom can't be bigger than 11
        zoom = min(11, zoom)

        # Zoom can't be smaller than 0
        zoom = max(0, zoom)

        if self.verbose:
            print(
                "😎 Please use `ax.set_extent` before increasing Zoom level for faster plotting."
            )
        stamen_terrain = cimgt.Stamen(style)
        self.ax.add_image(stamen_terrain, zoom)

        if alpha < 1:
            # Need to manually put a white layer over the STAMEN terrain
            if self.theme == "dark":
                alpha_color = "k"
            else:
                alpha_color = "w"
            poly = self.ax.projection.domain
            self.ax.add_feature(
                feature.ShapelyFeature([poly], self.ax.projection),
                color=alpha_color,
                alpha=1 - alpha,
                zorder=1,
            )
        if self.verbose == "debug":
            print("🐛 STAMEN:", f"{style=}, {zoom=}, {alpha=}")

        return self

    def OSM(self, zoom: int = 1, alpha=1):
        """
        Add Open Street Map tiles as background image.

        When adding a tile product to a map, it might be better to add
        it to the map first, then set the map extent, then make a separate
        call to ``EasyMap()`` to add other features like roads and
        counties. The reason is because, if you add a tile map to

        Parameters
        ----------
        zoom : int
            Zoom level between 0 and ?.
        alpha : float
            Alpha value (transparency); a value between 0 and 1.
        """
        image = cimgt.OSM()
        self.ax.add_image(image, zoom)
        if alpha < 1:
            # Need to manually put a white layer over the STAMEN terrain
            if self.theme == "dark":
                alpha_color = "k"
            else:
                alpha_color = "w"
            poly = self.ax.projection.domain
            self.ax.add_feature(
                feature.ShapelyFeature([poly], self.ax.projection),
                color=alpha_color,
                alpha=1 - alpha,
                zorder=1,
            )
        if self.verbose == "debug":
            print("🐛 OSM:", f"{zoom=}, {alpha=}")

        return self

    def STOCK(self, **kwargs):
        """Show stock image background (suitable for full-globe images)."""
        self.ax.stock_img()
        return self

    def NASA(
        self,
        DATE,
        layer="VIIRS_NOAA20_CorrectedReflectance_TrueColor",
        pixels=1000,
    ):
        """Add NASA image from Global Imagery Browse Service (GIBS).

        Parameters
        ----------
        DATE : date or datetime
            The a date for the image.
        layer : str
            The layer to add. Default is NOAA20 TrueColor. Others may
            be found at https://nasa-gibs.github.io/gibs-api-docs/available-visualizations/,
            or look at the URL for any map on NASA's Worldview tool
            https://worldview.earthdata.nasa.gov/

            - VIIRS_SNPP_L2_Sea_Surface_Temp_Day
            - MODIS_Terra_SurfaceReflectance_Bands143
            - MODIS_Combined_L3_White_Sky_Albedo_Daily
            - OrbitTracks_NOAA-20_Ascending

        pixels : int
            I don't actually think this number is pixels, but it is the number
            used at the HEIGHT and WIDTH argument in the URL. Larger number is
            higher resolution image.
        """
        try:
            from skimage import io
        except ImportError:
            raise ImportError(
                "Requires skimage; try `conda install -c conda-forge scikit-image`."
            )

        # Get Image
        proj4326 = (
            "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?version=1.3.0"
            "&service=WMS"
            "&request=GetMap"
            "&format=image/png"
            "&STYLE=default"
            "&bbox=-90,-180,90,180"
            "&CRS=EPSG:4326"
            f"&HEIGHT={pixels}"
            f"&WIDTH={pixels}"
            f"&TIME={DATE:%Y-%m-%d}"
            f"&layers={layer}"
        )

        # Display image on map.
        self.ax.imshow(
            io.imread(proj4326),
            transform=pc,
            extent=(-180, 180, -90, 90),
            origin="upper",
        )

        return self

    # ==================
    # Other map elements
    def DOMAIN(
        self,
        x,
        y=None,
        *,
        text: Optional[str] = None,
        method: Literal["fill", "cutout", "border"] = "cutout",
        facealpha: Union[Literal[0], Literal[1], float] = 0.25,
        text_kwargs={},
        **kwargs,
    ):
        """
        Add a polygon of the domain boundary to a map.

        The border is drawn from the outside values of the latitude and
        longitude xarray coordinates or numpy array.
        Lat/lon values should be given as degrees.

        Parameters
        ----------
        x : xarray.Dataset or numpy.ndarray
            If xarray, then should contain 'latitude' and 'longitude' coordinate.
            If numpy, then 2D numpy array for longitude and `y` arg is required.
        y : numpy.ndarray
            Only required if x is a numpy array.
            A numpy array of latitude values.
        text : str
            If not None, puts the string in the bottom left.
        method : {'fill', 'cutout', 'border'}
            Plot the domain as a filled area Polygon, a Cutout from the
            map, or as a simple border.
        facealpha : float between 0 and 1
            Since there isn't a "facealpha" attribute for plotting,
            this will be it.
        polygon_only : bool
            - True: Only return the polygons and don't plot on axes.
        """
        _method = {"fill", "cutout", "border"}
        assert method in _method, f"Method must be one of {_method}."

        ####################################################################
        # Determine how to handle output...xarray or numpy
        if isinstance(x, (xr.core.dataset.Dataset, xr.core.dataarray.DataArray)):
            if self.verbose:
                print("process input as xarray")

            if "latitude" in x.coords:
                x = x.rename({"latitude": "lat", "longitude": "lon"})
            LON = x.lon.data
            LAT = x.lat.data

        elif isinstance(x, np.ndarray):
            assert y is not None, "Please supply a value for x and y"
            if self.verbose:
                print("process input as numpy array")
            LON = x
            LAT = y
        else:
            raise ValueError("Review your input")
        ####################################################################

        # Path of array outside border starting from the lower left corner
        # and going around the array counter-clockwise.
        outside = (
            list(zip(LON[0, :], LAT[0, :]))
            + list(zip(LON[:, -1], LAT[:, -1]))
            + list(zip(LON[-1, ::-1], LAT[-1, ::-1]))
            + list(zip(LON[::-1, 0], LAT[::-1, 0]))
        )
        outside = np.array(outside)

        ## Polygon in latlon coordinates
        ## -----------------------------
        x = outside[:, 0]
        y = outside[:, 1]
        domain_polygon_latlon = sgeom.Polygon(zip(x, y))

        ## Polygon in projection coordinates
        ## ----------------------------------
        transform = self.ax.projection.transform_points(pc, x, y)

        # Remove any points that run off the projection map (i.e., point's value is `inf`).
        transform = transform[~np.isinf(transform).any(axis=1)]

        # These are the x and y points we need to create the Polygon for
        x = transform[:, 0]
        y = transform[:, 1]

        domain_polygon = sgeom.Polygon(
            zip(x, y)
        )  # This is the boundary of the LAT/LON array supplied.
        global_polygon = (
            self.ax.projection.domain
        )  # This is the projection globe polygon
        cutout = global_polygon.difference(
            domain_polygon
        )  # This is the difference between the domain and glob polygon

        # Plot
        kwargs.setdefault("edgecolors", "k")
        kwargs.setdefault("linewidths", 1)
        if method == "fill":
            kwargs.setdefault("facecolor", (0, 0, 0, facealpha))
            self.ax.add_feature(
                feature.ShapelyFeature([domain_polygon], self.ax.projection),
                **kwargs,
            )
        elif method == "cutout":
            kwargs.setdefault("facecolor", (0, 0, 0, facealpha))
            self.ax.add_feature(
                feature.ShapelyFeature([cutout], self.ax.projection), **kwargs
            )
        elif method == "border":
            kwargs.setdefault("facecolor", "none")
            self.ax.add_feature(
                feature.ShapelyFeature([domain_polygon.exterior], self.ax.projection),
                **kwargs,
            )

        if text:
            text_kwargs.setdefault("verticalalignment", "bottom")
            text_kwargs.setdefault("fontsize", 15)
            xx, yy = outside[0]
            self.ax.text(xx + 0.2, yy + 0.2, text, transform=pc, **text_kwargs)

        self.domain_polygon = domain_polygon
        self.domain_polygon_latlon = domain_polygon_latlon
        return self

    def INSET_GLOBE(self, **kwargs):
        """Add an axis showing a global inset map."""
        return inset_global_map(self.ax, **kwargs)
