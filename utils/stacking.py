from __future__ import annotations

from pathlib import Path


def _transforms_match(left, right, precision=9):
    return left.almost_equals(right, precision=precision)


def stack_annual_rasters(
    annual_rasters: list[Path | None],
    years: list[int],
    output_path: Path,
    nodata: int,
) -> Path:
    import rasterio
    import numpy as np
    from rasterio.enums import Resampling
    from rasterio.warp import reproject

    if not annual_rasters:
        raise ValueError("No annual rasters were provided for stacking.")
    if len(annual_rasters) != len(years):
        raise ValueError("The number of rasters must match the number of years.")
    available_rasters = [raster_path for raster_path in annual_rasters if raster_path is not None]
    if not available_rasters:
        raise ValueError("No real annual rasters were available for stacking.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(available_rasters[0]) as src0:
        profile = src0.profile.copy()
        profile.update(count=len(annual_rasters), nodata=nodata)
        reference_shape = (src0.height, src0.width)
        reference_transform = src0.transform
        reference_crs = src0.crs
        reference_dtype = src0.dtypes[0]

    for raster_path in available_rasters[1:]:
        with rasterio.open(raster_path) as src:
            if src.crs != reference_crs:
                raise ValueError(f"CRS mismatch in {raster_path}")
            if src.dtypes[0] != reference_dtype:
                raise ValueError(f"Dtype mismatch in {raster_path}")

    with rasterio.open(output_path, "w", **profile) as dest:
        for band_index, (raster_path, year) in enumerate(zip(annual_rasters, years), start=1):
            if raster_path is None:
                data = np.full(reference_shape, nodata, dtype=profile["dtype"])
            else:
                with rasterio.open(raster_path) as src:
                    if (
                        (src.height, src.width) == reference_shape
                        and src.crs == reference_crs
                        and _transforms_match(src.transform, reference_transform)
                    ):
                        data = src.read(1)
                    else:
                        data = np.full(reference_shape, nodata, dtype=profile["dtype"])
                        reproject(
                            source=rasterio.band(src, 1),
                            destination=data,
                            src_transform=src.transform,
                            src_crs=src.crs,
                            src_nodata=src.nodata,
                            dst_transform=reference_transform,
                            dst_crs=reference_crs,
                            dst_nodata=nodata,
                            resampling=Resampling.nearest,
                        )
                dest.write(data, band_index)
            dest.set_band_description(band_index, str(year))

    return output_path
