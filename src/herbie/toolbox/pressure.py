"""Pressure calculations."""

import numpy as np


def pres_to_alt(p_hPa, h_m):
    """
    Convert a station pressure and height to an altimeter reading.

    Follows the NOAA conversion found here:
    http://www.wrh.noaa.gov/slc/projects/wxcalc/formulas/altimeterSetting.pdf
    Input:
        p_hPa - station pressure in hPa
        h_m - station height in meters
    Output:
        calculated altimeter value in hPa
    """
    c = 0.190284  # Some constant. Not sure what from

    alt_hPa = (p_hPa - 0.3) * (
        1 + ((1013.25**c * 0.0065 / 288) * (h_m / (p_hPa - 0.3) ** c))
    ) ** (1 / c)
    return alt_hPa


def alt_to_pres(alt_hPa, h_m):
    """
    Convert a station altimeter and height to pressure.

    Follows the NOAA conversion found here:
    http://www.crh.noaa.gov/images/epz/wxcalc/stationPressure.pdf
    Input:
        alt_hPa - altimeter in hPa
        h_m - station elevation in meters
    Output:
        pres_hPa - station pressure in hPa
    """
    # The equation altimeter must be in inHg. Convert the presure hPa to inHg
    alt_inHg = 0.0295300 * alt_hPa

    pres_inHg = alt_inHg * ((288 - 0.0065 * h_m) / 288) ** 5.2561

    # Convert presure back to hPa
    pres_hPa = 33.8639 * pres_inHg

    return pres_hPa


def saturation_vapor_pressure(tmp_C):
    """
    Calculate saturation vapor pressure.

    Source:
        Rogers and Yau "Short Course in Cloud Physics" Equation 2.17
    Equation: Empirical fit to the integrated Clausius-Clapeyron equation
        Saturation Vapor Pressure (es) = 6.112 * exp((17.67T) / (T+243.5)
        Where T is temperature in Celsius and es is in hPa
    """
    es = 6.112 * np.exp((17.67 * tmp_C) / (tmp_C + 243.5))
    return es  # returned units in hPa


def saturation_vapor_pressure_NEW(tmp_C):
    """
    Calculate saturation vapor pressure.

    Source: A Simple Accurate Formula for Calculating Saturation Vapor Pressure of Water and Ice (Huang 2018)
            https://journals.ametsoc.org/doi/full/10.1175/JAMC-D-17-0334.1

    Equation: Empirical fit to integrated Clausius-Clapeyron equation

    Input : Temperature in Degrees Celsius
    Output: Saturation Vapor Pressure in hPa (millibars)
    """
    if tmp_C > 0:
        print("--> Saturation vapor pressure over water")
        Ps = np.exp(34.494 - (4924.99 / (tmp_C + 237.1))) / ((tmp_C + 105) ** 1.57)
    else:
        print("--> Saturation vapor pressure over ice")
        Ps = np.exp(43.494 - (6545.8 / (tmp_C + 278))) / ((tmp_C + 868) ** 2)

    return Ps / 100  # returned in hPa


def vapor_pressure_deficit(tmp_C, RH):
    """
    Calculate vapor pressure deficit.

        vpd = es * (100-RH)/100

    Why this is a meaningful measurement:
    "The strain under which an organism is placed in maintaining a
    water balance during temperature changes is much more clearly shown
    by noting the vapor pressure deficit than by recording the relative
    humidity."

    Reference
    ---------
    https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit/35022#35022?newreg=1550370399fc4ae183515472df76c113

        Anderson, D. B. 1936. Relative humidity or vapor pressure deficit.
        Ecology 17, no. 2: 277-282.


    """
    vpd = saturation_vapor_pressure(tmp_C) * (100 - RH) / 100.0
    return vpd
