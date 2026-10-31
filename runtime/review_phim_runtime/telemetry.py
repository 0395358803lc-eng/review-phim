"""Read-only NVIDIA/CPU sampling contract for the authorized Windows host.

The launcher is injected by an approved device adapter. This module never
starts processes at import time or loads film/media/model data.
"""
import csv
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

# These argument vectors are fixed: no user-provided paths or shell expansion.
TELEMETRY_CPU_ARGV = (
    'powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
    "$ErrorActionPreference='Stop'; "
    "$v=@(Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage); "
    "if ($v.Count -eq 0 -or $v -contains $null) { throw 'No CPU load observation' }; "
    "[math]::Round(($v | Measure-Object -Average).Average,2)"
)
TELEMETRY_GPU_ARGV = (
    'nvidia-smi',
    '--query-gpu=name,memory.total,memory.free,driver_version,utilization.gpu',
    '--format=csv,noheader,nounits',
)


@dataclass(frozen=True)
class GpuTelemetry:
    name: str
    total_mib: int
    free_mib: int
    driver_version: str
    utilization_pct: float


@dataclass(frozen=True)
class TelemetrySnapshot:
    device_id: str
    observed_at: datetime
    gpu_name: str
    vram_total_mib: int
    vram_free_mib: int
    logical_processors: int
    cpu_utilization_pct: float | None
    gpu_utilization_pct: float | None


def parse_nvidia_csv(raw: str) -> GpuTelemetry:
    """Reject multiple GPUs until there is an explicit GPU selector/binding."""
    import math
    rows = list(csv.reader(raw.splitlines(), skipinitialspace=True))
    if len(rows) != 1 or len(rows[0]) != 5:
        raise ValueError('Need exactly one GPU with five metrics')
    name, total, free, driver, utilization = (x.strip() for x in rows[0])
    if not name or not driver:
        raise ValueError('Missing GPU identity')
    total_i, free_i, utilization_f = int(total), int(free), float(utilization)
    if (total_i <= 0 or free_i < 0 or free_i > total_i
            or not math.isfinite(utilization_f) or not 0 <= utilization_f <= 100):
        raise ValueError('Invalid GPU resource figures')
    return GpuTelemetry(name, total_i, free_i, driver, utilization_f)


def collect_telemetry(device_id: str, runner: Callable, *, approved: bool,
                      now: datetime, logical_processors: int = 0) -> TelemetrySnapshot | None:
    """Sample fixed non-media commands; never synthesize missing GPU readings."""
    if (approved is not True or not isinstance(device_id, str) or not device_id.strip()
            or type(logical_processors) is not int or logical_processors <= 0
            or not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None):
        return None
    try:
        cpu = runner(TELEMETRY_CPU_ARGV)
        gpu = runner(TELEMETRY_GPU_ARGV)
        if cpu['returncode'] != 0 or gpu['returncode'] != 0:
            return None
        cpu_pct = float(cpu['stdout'].strip())
        from math import isfinite
        if not isfinite(cpu_pct) or not 0 <= cpu_pct <= 100:
            return None
        observed = parse_nvidia_csv(gpu['stdout'])
    except (KeyError, TypeError, ValueError, OSError, RuntimeError):
        return None
    return TelemetrySnapshot(device_id.strip(), now, observed.name, observed.total_mib,
                             observed.free_mib, logical_processors, cpu_pct,
                             observed.utilization_pct)
