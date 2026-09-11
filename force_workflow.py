"""prepare, run, postprocess, stack, and all.
python force_workflow.py prepare \
  --aoi /drive_mount/3DTests/data/DSWI_elina/UG_3035/UG_1polygon_3035.shp \
  --sensor sentinel2 \
  --stat median \
  --window apr_oct \
  --year 2018 \
  --list
"""


import argparse
import glob
from pathlib import Path

from utils.external_ndvi import (
    DEFAULT_BIGTIFF,
    DEFAULT_BLOCKSIZE,
    DEFAULT_COMPRESSION,
    DEFAULT_ZLEVEL,
    create_folder_structure,
    execute_cmd,
    export_ndvi_p90_product,
    force_class_udf,
)
from utils.stacking import stack_annual_rasters


base_path = "/drive_mount"
project_prefix = "elina_dswi"
force_dir = "/force:/force"
local_dir = "/drive_mount:/drive_mount"
hold = False

default_aoi_glob = "/drive_mount/process/data/elina_dswi/UG_1polygon_3035.shp"

# Defaults stop at 2025 because today is 2026-08-21 and the 2026 April-October window is not complete yet.
sentinel2_apr_may_years = list(range(2016, 2026))
sentinel2_apr_oct_years = list(range(2015, 2026))
landsat_years = list(range(1984, 2026))

chunk_size = "3000 3000"
version = "v1_0"
python_type = "CHUNK"
spectral_adjust = True

create_parameter_files = True
run_force_jobs = True
rerun_partial_jobs = True
run_postprocess = True
stack_yearly_rasters = True
allow_incomplete_stack = False
pad_missing_years = False

postprocess_num_threads = "ALL_CPUS"
postprocess_cachemax_mb = 1024
postprocess_build_overviews = True
postprocess_compression_method = DEFAULT_COMPRESSION
postprocess_bigtiff = DEFAULT_BIGTIFF
postprocess_zlevel = DEFAULT_ZLEVEL
postprocess_blocksize = DEFAULT_BLOCKSIZE
postprocess_output_nodata = -32768

PRODUCT_SPECS = [
    {
        "sensor_key": "sentinel2",
        "sensor_profile": "sentinel2",
        "force_sensors": ["SEN2A", "SEN2B"],
        "target_sensor": "SEN2L",
        "resolution": 10,
        "years": sentinel2_apr_may_years,
        "stack_years": sentinel2_apr_oct_years,
        "window_key": "apr_may",
        "window_label": "AprMay",
        "doy_range": "91 151",
        "stat_key": "median",
        "index_name": "DSWI_median",
        "udf_source": "utils/skel/udf_dswi_median_chunk.py",
    },
    {
        "sensor_key": "sentinel2",
        "sensor_profile": "sentinel2",
        "force_sensors": ["SEN2A", "SEN2B"],
        "target_sensor": "SEN2L",
        "resolution": 10,
        "years": sentinel2_apr_may_years,
        "stack_years": sentinel2_apr_oct_years,
        "window_key": "apr_may",
        "window_label": "AprMay",
        "doy_range": "91 151",
        "stat_key": "p20",
        "index_name": "DSWI_p20",
        "udf_source": "utils/skel/udf_dswi_p20_chunk.py",
    },
    {
        "sensor_key": "sentinel2",
        "sensor_profile": "sentinel2",
        "force_sensors": ["SEN2A", "SEN2B"],
        "target_sensor": "SEN2L",
        "resolution": 10,
        "years": sentinel2_apr_may_years,
        "stack_years": sentinel2_apr_oct_years,
        "window_key": "apr_may",
        "window_label": "AprMay",
        "doy_range": "91 151",
        "stat_key": "p80",
        "index_name": "DSWI_p80",
        "udf_source": "utils/skel/udf_dswi_p80_chunk.py",
    },
    {
        "sensor_key": "sentinel2",
        "sensor_profile": "sentinel2",
        "force_sensors": ["SEN2A", "SEN2B"],
        "target_sensor": "SEN2L",
        "resolution": 10,
        "years": sentinel2_apr_oct_years,
        "window_key": "apr_oct",
        "window_label": "AprOct",
        "doy_range": "91 304",
        "stat_key": "median",
        "index_name": "DSWI_median",
        "udf_source": "utils/skel/udf_dswi_median_chunk.py",
    },
    {
        "sensor_key": "sentinel2",
        "sensor_profile": "sentinel2",
        "force_sensors": ["SEN2A", "SEN2B"],
        "target_sensor": "SEN2L",
        "resolution": 10,
        "years": sentinel2_apr_oct_years,
        "window_key": "apr_oct",
        "window_label": "AprOct",
        "doy_range": "91 304",
        "stat_key": "p20",
        "index_name": "DSWI_p20",
        "udf_source": "utils/skel/udf_dswi_p20_chunk.py",
    },
    {
        "sensor_key": "sentinel2",
        "sensor_profile": "sentinel2",
        "force_sensors": ["SEN2A", "SEN2B"],
        "target_sensor": "SEN2L",
        "resolution": 10,
        "years": sentinel2_apr_oct_years,
        "window_key": "apr_oct",
        "window_label": "AprOct",
        "doy_range": "91 304",
        "stat_key": "p80",
        "index_name": "DSWI_p80",
        "udf_source": "utils/skel/udf_dswi_p80_chunk.py",
    },
    {
        "sensor_key": "landsat",
        "sensor_profile": "landsat",
        "force_sensors": ["LND05", "LND07", "LND08", "LND09"],
        "target_sensor": "SEN2L",
        "resolution": 30,
        "years": landsat_years,
        "window_key": "apr_may",
        "window_label": "AprMay",
        "doy_range": "91 151",
        "stat_key": "median",
        "index_name": "DSWI_median",
        "udf_source": "utils/skel/udf_dswi_median_chunk.py",
    },
    {
        "sensor_key": "landsat",
        "sensor_profile": "landsat",
        "force_sensors": ["LND05", "LND07", "LND08", "LND09"],
        "target_sensor": "SEN2L",
        "resolution": 30,
        "years": landsat_years,
        "window_key": "apr_may",
        "window_label": "AprMay",
        "doy_range": "91 151",
        "stat_key": "p20",
        "index_name": "DSWI_p20",
        "udf_source": "utils/skel/udf_dswi_p20_chunk.py",
    },
    {
        "sensor_key": "landsat",
        "sensor_profile": "landsat",
        "force_sensors": ["LND05", "LND07", "LND08", "LND09"],
        "target_sensor": "SEN2L",
        "resolution": 30,
        "years": landsat_years,
        "window_key": "apr_may",
        "window_label": "AprMay",
        "doy_range": "91 151",
        "stat_key": "p80",
        "index_name": "DSWI_p80",
        "udf_source": "utils/skel/udf_dswi_p80_chunk.py",
    },
    {
        "sensor_key": "landsat",
        "sensor_profile": "landsat",
        "force_sensors": ["LND05", "LND07", "LND08", "LND09"],
        "target_sensor": "SEN2L",
        "resolution": 30,
        "years": landsat_years,
        "window_key": "apr_oct",
        "window_label": "AprOct",
        "doy_range": "91 304",
        "stat_key": "median",
        "index_name": "DSWI_median",
        "udf_source": "utils/skel/udf_dswi_median_chunk.py",
    },
    {
        "sensor_key": "landsat",
        "sensor_profile": "landsat",
        "force_sensors": ["LND05", "LND07", "LND08", "LND09"],
        "target_sensor": "SEN2L",
        "resolution": 30,
        "years": landsat_years,
        "window_key": "apr_oct",
        "window_label": "AprOct",
        "doy_range": "91 304",
        "stat_key": "p20",
        "index_name": "DSWI_p20",
        "udf_source": "utils/skel/udf_dswi_p20_chunk.py",
    },
    {
        "sensor_key": "landsat",
        "sensor_profile": "landsat",
        "force_sensors": ["LND05", "LND07", "LND08", "LND09"],
        "target_sensor": "SEN2L",
        "resolution": 30,
        "years": landsat_years,
        "window_key": "apr_oct",
        "window_label": "AprOct",
        "doy_range": "91 304",
        "stat_key": "p80",
        "index_name": "DSWI_p80",
        "udf_source": "utils/skel/udf_dswi_p80_chunk.py",
    },
]


def normalize_date_range(year):
    return f"{year}-01-01", f"{year}-12-31"


def product_key(spec):
    return f"{spec['sensor_key']}_{spec['window_key']}_{spec['stat_key']}"


def project_name_for(spec, year):
    return f"{project_prefix}_{product_key(spec)}_{year}"


def annual_result_root(spec):
    return Path(base_path) / "process" / "results" / product_key(spec) / "annual"


def stack_result_path(spec, aoi_path):
    aoi_stem = Path(aoi_path).stem
    return (
        Path(base_path)
        / "process"
        / "results"
        / product_key(spec)
        / "stack"
        / f"{spec['index_name']}_{spec['sensor_key']}_{spec['window_key']}_{aoi_stem}_{version}.tif"
    )


def annual_output_path(spec, year, aoi_path):
    aoi_stem = Path(aoi_path).stem
    return annual_result_root(spec) / f"{spec['index_name']}_{spec['sensor_key']}_{spec['window_key']}_{aoi_stem}_{year}_{version}.tif"


def resolve_force_sensors_for_year(spec, year):
    if spec["sensor_key"] != "landsat":
        return spec["force_sensors"]

    if year <= 1998:
        sensors = ["LND05"]
    elif year <= 2012:
        sensors = ["LND05", "LND07"]
    elif year <= 2019:
        sensors = ["LND07", "LND08"]
    elif year == 2020:
        sensors = ["LND08"]
    else:
        sensors = ["LND08", "LND09"]

    return [sensor for sensor in sensors if sensor in spec["force_sensors"]]


def tiles_root_for(spec, year, aoi_path):
    project_name = project_name_for(spec, year)
    return (
        Path(base_path)
        / "process"
        / "temp"
        / project_name
        / "FORCE"
        / Path(aoi_path).name
        / "tiles_tss"
    )


def has_force_output_tiles(spec, year, aoi_path):
    tiles_root = tiles_root_for(spec, year, aoi_path)
    if not tiles_root.exists():
        return False

    for tif_path in tiles_root.rglob("*.tif"):
        tif_name = tif_path.name
        if "_wms_" in tif_name:
            continue
        if tif_name.endswith("_PYP.tif") or tif_name.startswith(spec["index_name"]):
            return True
    return False


def run_year(spec, year, aoi_path):
    start_date, end_date = normalize_date_range(year)
    project_name = project_name_for(spec, year)
    time_label = f"{year}0101_{year}1231"
    udf_source_path = Path(__file__).resolve().parent / spec["udf_source"]
    force_sensors = resolve_force_sensors_for_year(spec, year)

    if create_parameter_files:
        force_class_udf(
            project_name=project_name,
            force_dir=force_dir,
            local_dir=local_dir,
            base_path=base_path,
            aois=[aoi_path],
            hold=hold,
            udf_source=str(udf_source_path),
            python_type=python_type,
        )

    params_path = (
        Path(base_path)
        / "process"
        / "temp"
        / project_name
        / "FORCE"
        / Path(aoi_path).name
        / "tsa_UDF.prm"
    )
    if not params_path.exists():
        raise FileNotFoundError(f"Missing FORCE parameter file: {params_path}")

    configure_param_file(
        params_path,
        start_date,
        end_date,
        chunk_size,
        spec["doy_range"],
        sensors=force_sensors,
        target_sensor=spec["target_sensor"],
        resolution=spec["resolution"],
        spectral_adjust=spectral_adjust,
        date_ignore_landsat_7="2019-12-31",
        above_noise=3,
        below_noise=0 if spec["sensor_key"] == "landsat" else 1,
        screen_qai="NODATA CLOUD_OPAQUE CLOUD_BUFFER CLOUD_CIRRUS CLOUD_SHADOW SNOW SUBZERO SATURATION",
    )

    output_path = annual_output_path(spec, year, aoi_path)
    if run_force_jobs:
        print(
            f"Running {product_key(spec)} {year} with sensors: "
            f"{' '.join(force_sensors)} at {spec['resolution']} m"
        )
        execute_cmd(str(params_path), hold, local_dir, force_dir)
        if not has_force_output_tiles(spec, year, aoi_path):
            print(
                f"No FORCE output tiles were produced for {product_key(spec)} "
                f"{year} and {Path(aoi_path).name}. Skipping downstream steps for this year."
            )
            return output_path, time_label, False

    produced_output = False
    if run_postprocess:
        if not has_force_output_tiles(spec, year, aoi_path):
            print(
                f"Skipping postprocess for {product_key(spec)} {year} and "
                f"{Path(aoi_path).name}: no FORCE output tiles were found."
            )
            return output_path, time_label, False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            export_ndvi_p90_product(
                base_path=base_path,
                project_name=project_name,
                basename=Path(aoi_path).name,
                aoi_path=aoi_path,
                output_dir=output_path.parent / f"tiles_{year}",
                vrt_output_path=output_path.with_suffix(".vrt"),
                final_output_path=output_path,
                report_path=output_path.with_name(output_path.stem + "_report.json"),
                dtype="int16",
                num_threads=postprocess_num_threads,
                cachemax_mb=postprocess_cachemax_mb,
                build_overviews=postprocess_build_overviews,
                compression_method=postprocess_compression_method,
                bigtiff=postprocess_bigtiff,
                zlevel=postprocess_zlevel,
                blocksize=postprocess_blocksize,
                output_nodata=postprocess_output_nodata,
            )
        except RuntimeError as error:
            if "No clipped tiles were produced" not in str(error):
                raise
            print(
                f"Skipping {product_key(spec)} {year} and {Path(aoi_path).name}: "
                "FORCE output is entirely nodata inside the AOI."
            )
            return output_path, time_label, False
        produced_output = output_path.exists()

    return output_path, time_label, produced_output


def set_param_value(params_path, key, value):
    lines = Path(params_path).read_text().splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key} = "):
            lines[index] = f"{key} = {value}"
            Path(params_path).write_text("\n".join(lines) + "\n")
            return
    raise ValueError(f"Parameter {key} not found in {params_path}")


def configure_param_file(
    params_path,
    start_date,
    end_date,
    chunk_size_value,
    doy_range_value,
    file_tile=None,
    *,
    sensors=None,
    target_sensor=None,
    resolution=None,
    spectral_adjust=None,
    date_ignore_landsat_7=None,
    above_noise=None,
    below_noise=None,
    screen_qai=None,
):
    set_param_value(params_path, "DATE_RANGE", f"{start_date} {end_date}")
    set_param_value(params_path, "DOY_RANGE", doy_range_value)
    set_param_value(params_path, "CHUNK_SIZE", chunk_size_value)
    set_param_value(params_path, "FILE_TILE", file_tile or "NULL")

    optional_values = {
        "SENSORS": " ".join(sensors) if sensors is not None else None,
        "TARGET_SENSOR": target_sensor,
        "RESOLUTION": resolution,
        "SPECTRAL_ADJUST": (
            str(spectral_adjust).upper() if spectral_adjust is not None else None
        ),
        "DATE_IGNORE_LANDSAT_7": date_ignore_landsat_7,
        "ABOVE_NOISE": above_noise,
        "BELOW_NOISE": below_noise,
        "SCREEN_QAI": screen_qai,
    }
    for key, value in optional_values.items():
        if value is not None:
            set_param_value(params_path, key, value)


def build_stack_for_product(spec, aoi_path):
    requested_years = spec.get("stack_years", spec["years"]) if pad_missing_years else spec["years"]
    annual_rasters = []
    annual_years = []
    missing_years = []

    for year in requested_years:
        raster_path = annual_output_path(spec, year, aoi_path)
        if raster_path.exists():
            annual_rasters.append(raster_path)
            annual_years.append(year)
        else:
            missing_years.append(year)

    if missing_years and not allow_incomplete_stack and not pad_missing_years:
        print(
            f"Skipping stack for {product_key(spec)} and {Path(aoi_path).name}: "
            f"missing {len(missing_years)} year(s)."
        )
        return None

    if not annual_rasters:
        print(f"No annual rasters found for {product_key(spec)} and {Path(aoi_path).name}")
        return None

    output_path = stack_result_path(spec, aoi_path)
    if pad_missing_years:
        raster_by_year = {
            year: annual_output_path(spec, year, aoi_path)
            for year in requested_years
        }
        stacked_rasters = [
            raster_by_year[year] if raster_by_year[year].exists() else None
            for year in requested_years
        ]
        stacked_years = requested_years
    else:
        stacked_rasters = annual_rasters
        stacked_years = annual_years

    stacked = stack_annual_rasters(
        annual_rasters=stacked_rasters,
        years=stacked_years,
        output_path=output_path,
        nodata=postprocess_output_nodata,
    )
    print(f"Stack written: {stacked}")
    return stacked


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run DSWI yearly FORCE workflows in explicit modes."
    )
    parser.add_argument(
        "mode",
        choices=["prepare", "run", "postprocess", "stack", "all"],
        help=(
            "prepare=create/update FORCE parameter folders only; "
            "run=execute FORCE jobs; "
            "postprocess=export yearly rasters from existing FORCE tiles; "
            "stack=stack existing yearly rasters; "
            "all=prepare, run, postprocess, and stack in sequence"
        ),
    )
    parser.add_argument(
        "--aoi",
        action="append",
        help=(
            "Explicit AOI shapefile path. Repeat the flag to provide multiple AOIs. "
            "If omitted, the script falls back to the configured default AOI glob."
        ),
    )
    parser.add_argument(
        "--aoi-glob",
        help=(
            "Glob pattern for AOI shapefiles. "
            "If omitted, the script falls back to the configured default AOI glob."
        ),
    )
    parser.add_argument(
        "--sensor",
        choices=["sentinel2", "landsat"],
        help="Only run one sensor group.",
    )
    parser.add_argument(
        "--stat",
        choices=["median", "p20", "p80"],
        help="Only run one statistic.",
    )
    parser.add_argument(
        "--window",
        choices=["apr_may", "apr_oct"],
        help="Only run one seasonal window.",
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Only run one year.",
    )
    parser.add_argument(
        "--aoi-index",
        type=int,
        help="Only run one AOI by zero-based index from the configured AOI list.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the filtered products and AOIs, then exit without running FORCE.",
    )
    parser.add_argument(
        "--pad-missing-years",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "During stack, write nodata-only bands for requested years that have no "
            "annual raster (default: enabled). Use --no-pad-missing-years for strict "
            "stacking that skips products with missing years."
        ),
    )
    return parser


def resolve_mode_flags(mode):
    if mode == "prepare":
        return True, False, False, False
    if mode == "run":
        return False, True, False, False
    if mode == "postprocess":
        return False, False, True, False
    if mode == "stack":
        return False, False, False, True
    if mode == "all":
        return True, True, True, True
    raise ValueError(f"Unsupported mode: {mode}")


def filter_specs(specs, sensor=None, stat=None, window=None, year=None):
    filtered_specs = []
    for spec in specs:
        if sensor is not None and spec["sensor_key"] != sensor:
            continue
        if stat is not None and spec["stat_key"] != stat:
            continue
        if window is not None and spec["window_key"] != window:
            continue

        filtered_spec = dict(spec)
        if year is not None:
            if year not in spec["years"]:
                continue
            filtered_spec["years"] = [year]
        filtered_specs.append(filtered_spec)

    return filtered_specs


def filter_aois(configured_aois, aoi_index=None):
    if aoi_index is None:
        return configured_aois
    if aoi_index < 0 or aoi_index >= len(configured_aois):
        raise IndexError(
            f"AOI index {aoi_index} is out of range for {len(configured_aois)} configured AOI(s)."
        )
    return [configured_aois[aoi_index]]


def resolve_aois(args):
    if args.aoi:
        return [str(Path(aoi_path).resolve()) for aoi_path in args.aoi]
    if args.aoi_glob:
        return sorted(glob.glob(args.aoi_glob))
    return sorted(glob.glob(default_aoi_glob))


def print_selection_summary(specs, selected_aois):
    print(f"Selected AOIs: {len(selected_aois)}")
    for index, aoi_path in enumerate(selected_aois):
        print(f"  AOI[{index}]: {aoi_path}")

    print(f"Selected products: {len(specs)}")
    for spec in specs:
        year_summary = (
            str(spec["years"][0])
            if len(spec["years"]) == 1
            else f"{spec['years'][0]}-{spec['years'][-1]} ({len(spec['years'])} years)"
        )
        print(
            f"  {product_key(spec)} | sensor={spec['sensor_key']} | "
            f"window={spec['window_key']} | stat={spec['stat_key']} | years={year_summary}"
        )


def main(argv=None):
    global create_parameter_files
    global run_force_jobs
    global run_postprocess
    global stack_yearly_rasters
    global pad_missing_years

    parser = build_parser()
    args = parser.parse_args(argv)
    (
        create_parameter_files,
        run_force_jobs,
        run_postprocess,
        stack_yearly_rasters,
    ) = resolve_mode_flags(args.mode)
    pad_missing_years = args.pad_missing_years

    resolved_aois = resolve_aois(args)
    if not resolved_aois:
        raise FileNotFoundError("No AOI shapefiles matched the configured glob pattern.")

    selected_aois = filter_aois(resolved_aois, args.aoi_index)
    selected_specs = filter_specs(
        PRODUCT_SPECS,
        sensor=args.sensor,
        stat=args.stat,
        window=args.window,
        year=args.year,
    )
    if not selected_specs:
        raise ValueError("No products matched the selected filters.")

    create_folder_structure(base_path)
    print(
        f"Mode: {args.mode} | "
        f"create_parameter_files={create_parameter_files} | "
        f"run_force_jobs={run_force_jobs} | "
        f"run_postprocess={run_postprocess} | "
        f"stack_yearly_rasters={stack_yearly_rasters} | "
        f"pad_missing_years={pad_missing_years}"
    )
    print_selection_summary(selected_specs, selected_aois)
    if args.list:
        return

    for spec in selected_specs:
        print(f"Processing product: {product_key(spec)}")
        for aoi_path in selected_aois:
            for year in spec["years"]:
                annual_output, _, produced_output = run_year(spec, year, aoi_path)
                if produced_output:
                    print(f"Created annual raster for {year}: {annual_output}")
                elif create_parameter_files:
                    print(f"Prepared FORCE job for {year}: {annual_output}")
                elif run_force_jobs:
                    print(f"Executed FORCE job for {year}: {annual_output}")
                elif run_postprocess:
                    print(f"Postprocess attempted for {year}: {annual_output}")

            if stack_yearly_rasters and run_postprocess:
                build_stack_for_product(spec, aoi_path)
            elif stack_yearly_rasters and not run_postprocess and args.mode == "stack":
                build_stack_for_product(spec, aoi_path)
            elif stack_yearly_rasters and not run_postprocess:
                print(
                    f"Skipping stack for {product_key(spec)} and {Path(aoi_path).name}: "
                    "run_postprocess is False, so no annual rasters were generated."
                )


if __name__ == "__main__":
    main()
