"""
Register custom color maps.

Custom color maps for standard meteorological variables with the necessary
bounds, ticks, and labels for building the colorbar.

National Weather Service standard color maps:

- Source: Joseph Moore <joseph.moore@noaa.gov>
- Document: references/NWS Standard Color Curve Summary.pdf

"""

try:
    import numpy as np
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
except ImportError:
    raise ImportError("herbie.paint requires matplotlib.")


def make_custom_cmaps(name, colors, bounds: list = None, N: int = None):
    if N is None:
        N = len(colors)
    linear_cmap = mcolors.LinearSegmentedColormap.from_list(name, colors)
    segment_cmap = mcolors.LinearSegmentedColormap.from_list(name + "2", colors, N=N)

    # When data is NaN, set color to transparent
    linear_cmap.set_bad("#ffffff00")
    segment_cmap.set_bad("#ffffff00")

    for cm in [linear_cmap, segment_cmap]:
        mpl.colormaps.register(cmap=cm, force=True)
        mpl.colormaps.register(cmap=cm.reversed(), force=True)

    if bounds is not None:
        return (
            mcolors.Normalize(bounds.min(), bounds.max()),
            mcolors.BoundaryNorm(bounds, linear_cmap.N),
        )


# ======================================================================
# National Weather Service proposed standard color curves (2018)
# ======================================================================


class NWSTemperature:
    name = "nws.tmp"
    units = r"$\degree$C"
    variable = "Temperature"
    colors = np.array(
        [
            "#91003f",
            "#ce1256",
            "#e7298a",
            "#df65b0",
            "#ff73df",
            "#ffbee8",
            "#ffffff",
            "#dadaeb",
            "#bcbddc",
            "#9e9ac8",
            "#756bb1",
            "#54278f",
            "#0d007d",
            "#0d3d9c",
            "#0066c2",
            "#299eff",
            "#4ac7ff",
            "#73d7ff",
            "#adffff",
            "#30cfc2",
            "#009996",
            "#125757",
            "#066d2c",
            "#31a354",
            "#74c476",
            "#a1d99b",
            "#d3ffbe",
            "#ffffb3",
            "#ffeda0",
            "#fed176",
            "#feae2a",
            "#fd8d3c",
            "#fc4e2a",
            "#e31a1c",
            "#b10026",
            "#800026",
            "#590042",
            "#280028",
        ]
    )
    # NWS bounds in Fahrenheit
    bounds = np.linspace(-65, 125, len(colors) + 1)
    # Convert to Celsius (approximate)
    bounds = (bounds - 30) / 2
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds[1::2])


class NWSWindChill:
    """National Weather Service Wind Chill colormap properties.

    Identical to NWSHeatIndex.
    """

    name = "nws.wind_chill"
    units = r"$\degree$C"
    variable = "Wind Chill"
    colors = np.array(
        [
            "#91003f",
            "#ce1256",
            "#e7298a",
            "#df65b0",
            "#ff73df",
            "#ffbee8",
            "#ffffff",
            "#dadaeb",
            "#bcbddc",
            "#9e9ac8",
            "#756bb1",
            "#54278f",
            "#0d007d",
            "#0d3d9c",
            "#0066c2",
            "#299eff",
            "#4ac7ff",
            "#73d7ff",
            "#adffff",
            "#30cfc2",
            "#009996",
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#ffeda0",
            "#fed176",
            "#feae2a",
            "#fd8d3c",
            "#fc4e2a",
            "#e31a1c",
            "#b10026",
            "#800026",
            "#590042",
            "#280028",
        ]
    )
    # NWS bounds in Fahrenheit
    bounds = np.linspace(-65, 125, len(colors) + 1)
    # Convert to Celsius (approximate)
    bounds = (bounds - 30) / 2
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds[1::2])


class NWSHeatIndex:
    """Identical to NWSWindChill."""

    name = "nws.heat_index"
    units = r"$\degree$C"
    variable = "Heat Index"
    colors = np.array(
        [
            "#91003f",
            "#ce1256",
            "#e7298a",
            "#df65b0",
            "#ff73df",
            "#ffbee8",
            "#ffffff",
            "#dadaeb",
            "#bcbddc",
            "#9e9ac8",
            "#756bb1",
            "#54278f",
            "#0d007d",
            "#0d3d9c",
            "#0066c2",
            "#299eff",
            "#4ac7ff",
            "#73d7ff",
            "#adffff",
            "#30cfc2",
            "#009996",
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#dcdcdc",  # grey
            "#ffeda0",
            "#fed176",
            "#feae2a",
            "#fd8d3c",
            "#fc4e2a",
            "#e31a1c",
            "#b10026",
            "#800026",
            "#590042",
            "#280028",
        ]
    )
    # NWS bounds in Fahrenheit
    bounds = np.linspace(-65, 125, len(colors) + 1)
    # Convert to Celsius (approximate)
    bounds = (bounds - 30) / 2
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds[1::2])


class NWSDewPointTemperature:
    name = "nws.dpt"
    units = r"$\degree$C"
    variable = "Dew Point"
    colors = np.array(
        [
            "#3b2204",
            "#543005",
            "#8c520a",
            "#bf812d",
            "#cca854",
            "#dfc27d",
            "#e6d9b5",
            "#d3ebe7",
            "#a9dbd3",
            "#72b8ad",
            "#318c85",
            "#01665f",
            "#003c30",
            "#002921",
        ]
    )
    # NWS bounds in F
    bounds = np.array([-10, 0, 10, 20, 30, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85])
    # convert to C (approximate)
    bounds = (bounds - 30) / 2
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds)


class NWSRelativeHumidity:
    name = "nws.rh"
    units = "%"
    variable = "Relative Humidity"
    colors = np.array(
        [
            "#910022",
            "#a61122",
            "#bd2e24",
            "#d44e33",
            "#e36d42",
            "#fa8f43",
            "#fcad58",
            "#fed884",
            "#fff2aa",
            "#e6f49d",
            "#bce378",
            "#71b55c",
            "#26914b",
            "#00572e",
        ]
    )
    bounds = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100])
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds)


class NWSWindSpeed:
    name = "nws.wind"
    units = r"m s$\mathregular{^{-1}}$"
    variable = "Wind Speed"
    colors = np.array(
        [
            "#103f78",
            "#225ea8",
            "#1d91c0",
            "#41b6c4",
            "#7fcdbb",
            "#b4d79e",
            "#dfff9e",
            "#ffffa6",
            "#ffe873",
            "#ffc400",
            "#ffaa00",
            "#ff5900",
            "#ff0000",
            "#a80000",
            "#6e0000",
            "#ffbee8",
            "#ff73df",
        ]
    )
    # MPH
    bounds = np.array(
        [0.0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 100, 120, 140, 160]
    )
    # Convert to m/s (approximate)
    bounds *= 0.5
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds)


class NWSCloudCover:
    name = "nws.cloud"
    units = "%"
    variable = "Cloud Cover"
    colors = np.array(
        [
            "#24a0f2",
            "#4eb0f2",
            "#80b7f8",
            "#a0c8ff",
            "#d2e1ff",
            "#e1e1e1",
            "#c9c9c9",
            "#a5a5a5",
            "#6e6e6e",
            "#505050",
        ]
    )
    bounds = np.linspace(0, 100, len(colors) + 1)
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds)


class NWSProbabilityOfPrecipitation:
    name = "nws.pop"
    units = "%"
    variable = "Probability of Precipitation"
    colors = np.array(
        [
            "#f5f5f5",
            "#e2f6da",
            "#d5f2ca",
            "#c0ebaf",
            "#98df7b",
            "#6fd349",
            "#43c634",
            "#23b70b",
            "#139e07",
            "#0b8403",
        ]
    )
    bounds = np.linspace(0, 100, len(colors) + 1)
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds)


class NWSProbabilityOfPrecipitationSnow:
    name = "nws.pop_snow"
    units = "%"
    variable = "Probability of Snow"
    colors = np.array(
        [
            "#f5f5f5",
            "#e3ebff",
            "#bdd6ff",
            "#94b8ff",
            "#66a3ff",
            "#3690ff",
            "#0a7afa",
            "#006bd6",
            "#004ead",
            "#002487",
        ]
    )
    bounds = np.linspace(0, 100, len(colors) + 1)
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds)


class NWSProbabilityOfPrecipitationIce:
    name = "nws.pop_ice"
    units = "%"
    variable = "Probability of Ice"
    colors = np.array(
        [
            "#f5f5f5",
            "#ffd9ed",
            "#ffaafa",
            "#ff83f9",
            "#ff57f7",
            "#ff37f5",
            "#e619f9",
            "#d500fd",
            "#a200ad",
            "#640087",
        ]
    )
    bounds = np.linspace(0, 100, len(colors) + 1)
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds[1::2])


class NWSPrecipitation:
    """National Weather Service precipitation amount colorbar properties.

    Also known as Qualitative Precipitation Forecast/Estimate (QPF/QPE).
    """

    name = "nws.pcp"
    units = "mm"
    variable = "Precipitation"
    colors = np.array(
        [
            "#ffffff",
            "#c7e9c0",
            "#a1d99b",
            "#74c476",
            "#31a353",
            "#006d2c",
            "#fffa8a",
            "#ffcc4f",
            "#fe8d3c",
            "#fc4e2a",
            "#d61a1c",
            "#ad0026",
            "#700026",
            "#3b0030",
            "#4c0073",
            "#ffdbff",
        ]
    )
    # NWS bounds in inches
    bounds = np.array(
        [0, 0.01, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 10, 15, 20, 30, 50]
    )
    # Convert to mm (approximate)
    bounds *= 25
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="uniform", ticks=bounds)


class NWSPrecipitationSnow:
    name = "nws.pcp_snow"
    units = "mm"
    variable = "Snow"
    colors = np.array(
        [
            "#ffffff",
            "#bdd7e7",
            "#6baed6",
            "#3182bd",
            "#08519c",
            "#082694",
            "#ffff96",
            "#ffc400",
            "#ff8700",
            "#db1400",
            "#9e0000",
            "#690000",
            "#360000",
        ]
    )
    # NWS bounds in inches
    bounds = np.array([0, 0.1, 1, 2, 3, 4, 6, 8, 12, 18, 24, 30, 36, 42])
    # Convert to mm (approximate)
    bounds *= 25
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="uniform", ticks=bounds)


class NWSPrecipitationIce:
    name = "nws.pcp_ice"
    units = "mm"
    variable = "Ice"
    colors = np.array(
        [
            "#f3ea3b",
            "#ffc000",
            "#ff0000",
            "#c00000",
            "#9966ff",
            "#720ac8",
            "#24055b",
        ]
    )
    # NWS bounds in inches
    bounds = np.array([0.01, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 3.0])
    # convert to mm (approximate)
    bounds *= 25
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="uniform", ticks=bounds)


class NWSWaveHeight:
    name = "nws.wave"
    units = "m"
    variable = "Wave Height"
    colors = np.array(
        [
            "#ebfdff",
            "#abedf5",
            "#78cdd6",
            "#4bb8c4",
            "#55b59f",
            "#86d483",
            "#b0e890",
            "#ddff99",
            "#fed976",
            "#feb24c",
            "#fd8d3c",
            "#fc4e2a",
            "#e31a1c",
            "#bd0026",
            "#800026",
            "#5c002f",
            "#330023",
        ]
    )
    # NWS bounds in feet
    bounds = np.array(
        [0.0, 1, 2, 3, 4, 5, 7, 10, 12, 15, 20, 25, 30, 35, 40, 50, 60, 70], dtype=float
    )
    # convert to meters (approximate)
    bounds *= 0.3
    norm, norm2 = make_custom_cmaps(name, colors, bounds)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
    kwargs = dict(cmap=cmap, norm=norm)
    kwargs2 = dict(cmap=cmap, norm=norm2)
    cbar_kwargs = dict(label=f"{variable} ({units})")
    cbar_kwargs2 = cbar_kwargs | dict(spacing="proportional", ticks=bounds)


# ======================================================================
# Terrain height and land cover
# ======================================================================


class LandTan:
    name = "land.tan"
    cmap = mcolors.LinearSegmentedColormap.from_list(
        name,
        [
            (0, "#f8b893"),
            (0.4, "#c0784f"),
            (0.6, "#97674c"),
            (0.85, "#6b3d22"),
            (1, "#dadada"),
        ],
    )
    cmap.set_bad("#97b6e1")
    plt.colormaps.register(cmap, force=True)


class LandBrown:
    name = "land.brown"
    cmap = mcolors.LinearSegmentedColormap.from_list(
        name,
        [
            (0, "#ffad7d"),
            (0.5, "#b46f46"),
            (1, "#6b3d22"),
        ],
    )
    cmap.set_bad("#97b6e1")
    plt.colormaps.register(cmap, force=True)


class LandGreen:
    name = "land.green"
    cmap = mcolors.LinearSegmentedColormap.from_list(
        name,
        [
            (0.0, "yellowgreen"),
            (0.03, "darkgreen"),
            (0.08, "forestgreen"),
            (0.45, "wheat"),
            (0.60, "tan"),
            (0.95, "sienna"),
            (1.00, "snow"),
        ],
    )
    cmap.set_bad("#97b6e1")
    plt.colormaps.register(cmap, force=True)


class Water:
    name = "water"
    cmap = mcolors.LinearSegmentedColormap.from_list(
        name,
        [
            (0.0, "mediumblue"),
            (0.8, "deepskyblue"),
            (1, "#97b6e1"),
        ],
    )
    plt.colormaps.register(cmap, force=True)
    plt.colormaps.register(cmap.reversed(), force=True)


# ======================================================================
# Other
# ======================================================================

red = "#88211b"
blue = "#0c3576"
tan = "#f0ead2"
white = "#ffffff"
black = "#111111"


class HerbieWhite:
    name = "herbie.white"
    colors = [red, white, blue]
    make_custom_cmaps(name, colors, N=7)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")


class HerbieTan:
    name = "herbie.tan"
    colors = [red, tan, blue]
    make_custom_cmaps(name, colors, N=7)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")


class HerbieBlack:
    name = "herbie.black"
    colors = [red, black, blue]
    make_custom_cmaps(name, colors, N=7)
    cmap = plt.get_cmap(name)
    cmap2 = plt.get_cmap(name + "2")
