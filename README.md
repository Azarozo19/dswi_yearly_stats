# SITS DSWI Yearly Stats

FORCE-based workflow to generate yearly DSWI products and stack them into multi-band rasters where each band is one year.

This project produces 12 final rasters:

- Sentinel-2, April-May, `DSWI_median`
- Sentinel-2, April-May, `DSWI_p20`
- Sentinel-2, April-May, `DSWI_p80`
- Sentinel-2, April-October, `DSWI_median`
- Sentinel-2, April-October, `DSWI_p20`
- Sentinel-2, April-October, `DSWI_p80`
- Landsat 5/8/9, April-May, `DSWI_median`
- Landsat 5/8/9, April-May, `DSWI_p20`
- Landsat 5/8/9, April-May, `DSWI_p80`
- Landsat 5/8/9, April-October, `DSWI_median`
- Landsat 5/8/9, April-October, `DSWI_p20`
- Landsat 5/8/9, April-October, `DSWI_p80`

Processing model:

1. Run one FORCE UDF job per year.
2. Postprocess each year to one clipped annual raster.
3. Stack annual rasters into one final multi-band raster per product.

This design keeps the FORCE part simple and reuses the tested orchestration already available in `/rvt_mount/SITS_NDVI90pct`.

## Main Files

- [force_workflow.py](/rvt_mount/SITS_dswi_yearly_stats/force_workflow.py:1): yearly workflow and final stacking
- [utils/stacking.py](/rvt_mount/SITS_dswi_yearly_stats/utils/stacking.py:1): annual-raster stack builder
- [utils/external_ndvi.py](/rvt_mount/SITS_dswi_yearly_stats/utils/external_ndvi.py:1): loader for reusable helpers from `SITS_NDVI90pct`
- [utils/skel/udf_dswi_median_chunk.py](/rvt_mount/SITS_dswi_yearly_stats/utils/skel/udf_dswi_median_chunk.py:1): DSWI median UDF
- [utils/skel/udf_dswi_p20_chunk.py](/rvt_mount/SITS_dswi_yearly_stats/utils/skel/udf_dswi_p20_chunk.py:1): DSWI 20th percentile UDF
- [utils/skel/udf_dswi_p80_chunk.py](/rvt_mount/SITS_dswi_yearly_stats/utils/skel/udf_dswi_p80_chunk.py:1): DSWI 80th percentile UDF

## Configuration

Edit the block at the top of [force_workflow.py](/rvt_mount/SITS_dswi_yearly_stats/force_workflow.py:1):

- `default_aoi_glob`
- `sentinel2_years`
- `landsat_years`

Default periods:

- `apr_may`: DOY `91 151`
- `apr_oct`: DOY `91 304`

Default sensors:

- Sentinel-2: `SEN2A`, `SEN2B`, target `SEN2L`, 10 m
- Landsat: `LND05`, `LND08`, `LND09`, target `LNDLG`, 30 m

The Landsat default intentionally excludes `LND07`, because you explicitly asked for Landsat 5, 8, and 9 together.

Default year coverage in the current config is:

- Sentinel-2: 2015-2025
- Landsat: 1984-2025

The default stops at 2025 because the current date is August 21, 2026, so the 2026 April-October window is still incomplete.

## Run Modes

Run the script from the command line:

```bash
conda activate SITSclass
cd /rvt_mount/SITS_dswi_yearly_stats
python force_workflow.py <mode> --aoi /path/to/aoi.shp
```

Available modes:

- `prepare`: create/update FORCE parameter folders and `tsa_UDF.prm` files only
- `run`: execute FORCE jobs from existing parameter folders
- `postprocess`: export yearly rasters from existing FORCE tile outputs
- `stack`: stack existing yearly rasters into final multi-band products
- `all`: run prepare, run, postprocess, and stack in sequence

Typical usage:

```bash
python force_workflow.py prepare --aoi /path/to/aoi.shp
python force_workflow.py run --aoi /path/to/aoi.shp
python force_workflow.py postprocess --aoi /path/to/aoi.shp
python force_workflow.py stack --aoi /path/to/aoi.shp
```

or:

```bash
python force_workflow.py all --aoi /path/to/aoi.shp
```

## Debug One Case

To debug one small case, filter by sensor, metric, window, and year.

Inspect what would run:

```bash
python force_workflow.py prepare \
  --aoi /rvt_mount/3DTests/data/DSWI_elina/UG_3035/UG_1polygon_3035.shp \
  --sensor landsat \
  --stat p80 \
  --window apr_oct \
  --year 2018 \
  --list
```

Run only that one case:

```bash
python force_workflow.py prepare --aoi /rvt_mount/3DTests/data/DSWI_elina/UG_3035/UG_1polygon_3035.shp --sensor landsat --stat p80 --window apr_oct --year 2018
python force_workflow.py run --aoi /rvt_mount/3DTests/data/DSWI_elina/UG_3035/UG_1polygon_3035.shp --sensor landsat --stat p80 --window apr_oct --year 2018
python force_workflow.py postprocess --aoi /rvt_mount/3DTests/data/DSWI_elina/UG_3035/UG_1polygon_3035.shp --sensor landsat --stat p80 --window apr_oct --year 2018
python force_workflow.py stack --aoi /rvt_mount/3DTests/data/DSWI_elina/UG_3035/UG_1polygon_3035.shp --sensor landsat --stat p80 --window apr_oct
```

You can also target one AOI if multiple AOIs are configured:

```bash
python force_workflow.py prepare --aoi /rvt_mount/3DTests/data/DSWI_elina/UG_3035/UG_1polygon_3035.shp --sensor sentinel2 --stat median --window apr_may --year 2019
```

## Outputs

Annual rasters are written below:

```text
process/results/<product_key>/annual/
```

Final stacked rasters are written below:

```text
process/results/<product_key>/stack/
```

Band descriptions in the final raster are the calendar years.
