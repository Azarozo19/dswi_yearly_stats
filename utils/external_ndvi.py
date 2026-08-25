from __future__ import annotations

import importlib.util
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any


NDVI_REPO_ROOT = Path("/rvt_mount/SITS_NDVI90pct")
DEFAULT_COMPRESSION = "DEFLATE"
DEFAULT_ZLEVEL = "9"
DEFAULT_BIGTIFF = "YES"
DEFAULT_BLOCKSIZE = 512
DEFAULT_OVERVIEW_RESAMPLING = "nearest"
_MODULE_CACHE = {}


def _load_module(module_name: str, module_path: Path):
    cached = _MODULE_CACHE.get(module_name)
    if cached is not None:
        return cached

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _MODULE_CACHE[module_name] = module
    return module


def _force_class_utils():
    return _load_module(
        "sits_ndvi_force_class_utils",
        NDVI_REPO_ROOT / "utils" / "force_class_utils.py",
    )


def _utils():
    return _load_module(
        "sits_ndvi_utils",
        NDVI_REPO_ROOT / "utils" / "utils.py",
    )


def _strip_sudo_prefix(command: str) -> str:
    stripped = command.lstrip()
    if stripped.startswith("sudo "):
        return stripped[5:]
    return command


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@contextmanager
def _direct_xterm_bypass(module: Any):
    original_run = module.subprocess.run

    def patched_run(args, *pargs, **kwargs):
        if isinstance(args, (list, tuple)) and args:
            head = args[0]
            if head == "xterm":
                cmd = args[-1]
                if not isinstance(cmd, str):
                    raise ValueError(f"Unexpected xterm command payload: {args}")
                cmd = _strip_sudo_prefix(cmd)
                print("Running command directly instead of via xterm:")
                print(cmd)
                return original_run(["bash", "-lc", cmd], *pargs, **kwargs)
            if head == "bash" and len(args) >= 3 and args[1] == "-lc":
                patched_args = list(args)
                if isinstance(patched_args[2], str):
                    patched_args[2] = _strip_sudo_prefix(patched_args[2])
                return original_run(patched_args, *pargs, **kwargs)
        return original_run(args, *pargs, **kwargs)

    module.subprocess.run = patched_run
    try:
        yield
    finally:
        module.subprocess.run = original_run


def force_class_udf(*args, **kwargs):
    module = _force_class_utils()
    with _working_directory(NDVI_REPO_ROOT), _direct_xterm_bypass(module):
        return module.force_class_udf(*args, **kwargs)


def create_folder_structure(*args, **kwargs):
    return _utils().create_folder_structure(*args, **kwargs)


def execute_cmd(*args, **kwargs):
    module = _utils()
    original_run = module.subprocess.run

    def patched_run(command, *pargs, **run_kwargs):
        if isinstance(command, str):
            command = _strip_sudo_prefix(command)
        return original_run(command, *pargs, **run_kwargs)

    module.subprocess.run = patched_run
    try:
        return module.execute_cmd(*args, **kwargs)
    finally:
        module.subprocess.run = original_run


def export_ndvi_p90_product(*args, **kwargs):
    return _utils().export_ndvi_p90_product(*args, **kwargs)
