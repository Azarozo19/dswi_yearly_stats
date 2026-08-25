import warnings

import numpy as np


STAT_NAME = "DSWI_P80"
PERCENTILE = 80
SCALE_FACTOR = 100
_BAND_INDEX_CACHE = {}


def forcepy_init(dates, sensors, bandnames):
    return [STAT_NAME]


def _band_index(bandnames, primary_name, fallback_name=None):
    matches = np.argwhere(bandnames == primary_name)
    if matches.size:
        return matches[0][0]
    if fallback_name is not None:
        matches = np.argwhere(bandnames == fallback_name)
        if matches.size:
            return matches[0][0]
    raise ValueError(f"Required band not found: {primary_name!r}")


def _resolve_band_indices(bandnames):
    cache_key = tuple(bandnames.tolist())
    cached = _BAND_INDEX_CACHE.get(cache_key)
    if cached is not None:
        return cached

    green = _band_index(bandnames, b"GREEN")
    red = _band_index(bandnames, b"RED")
    nir = _band_index(bandnames, b"NIR", fallback_name=b"BROADNIR")
    swir1 = _band_index(bandnames, b"SWIR1")
    _BAND_INDEX_CACHE[cache_key] = (green, red, nir, swir1)
    return green, red, nir, swir1


def _write_statistic(inarray, outarray, bandnames, nodata):
    outarray[0][:] = nodata
    green, red, nir, swir1 = _resolve_band_indices(bandnames)

    green_values = inarray[:, green, :, :].astype(np.float32, copy=True)
    red_values = inarray[:, red, :, :].astype(np.float32, copy=True)
    nir_values = inarray[:, nir, :, :].astype(np.float32, copy=True)
    swir1_values = inarray[:, swir1, :, :].astype(np.float32, copy=True)

    for values in (green_values, red_values, nir_values, swir1_values):
        values[values == nodata] = np.nan

    denominator = red_values + swir1_values
    valid = np.isfinite(green_values) & np.isfinite(red_values)
    valid &= np.isfinite(nir_values) & np.isfinite(swir1_values)
    valid &= denominator != 0

    dswi = np.full_like(green_values, np.nan, dtype=np.float32)
    np.add(green_values, nir_values, out=dswi, where=valid)
    np.divide(dswi, denominator, out=dswi, where=valid)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered")
        stat = np.nanpercentile(dswi, PERCENTILE, axis=0)

    valid_pixels = np.isfinite(stat)
    if not np.any(valid_pixels):
        return

    outarray[0][valid_pixels] = np.rint(stat[valid_pixels] * SCALE_FACTOR)


def forcepy_chunk(inarray, outarray, dates, sensors, bandnames, nodata, nproc):
    _write_statistic(inarray, outarray, bandnames, nodata)


def forcepy_block(inarray, outarray, dates, sensors, bandnames, nodata, nproc):
    _write_statistic(inarray, outarray, bandnames, nodata)
