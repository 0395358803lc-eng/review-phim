"""In-memory admission prototype; not persistent and not a host daemon."""
from dataclasses import dataclass
import math
from datetime import datetime


@dataclass(frozen=True)
class ResourceSnapshot:
    vram_total_mib: int
    vram_free_mib: int
    logical_processors: int


@dataclass(frozen=True)
class ResourceLease:
    job_id: str
    gpu_mib: int
    cpu_workers: int
    heavy_gpu: bool


class BalancedScheduler:
    def __init__(self):
        self._leases: dict[str,ResourceLease] = {}

    def acquire(self, job_id: str, gpu_mib: int, cpu_workers: int,
                heavy_gpu: bool, snapshot: ResourceSnapshot) -> ResourceLease | None:
        if not job_id or job_id in self._leases or min(gpu_mib,cpu_workers) < 0:
            return None
        budget = max(0,min(math.floor(.75 * snapshot.vram_total_mib),snapshot.vram_free_mib - 1024))
        occupied_gpu = sum(x.gpu_mib for x in self._leases.values())
        occupied_cpu = sum(x.cpu_workers for x in self._leases.values())
        cpu_cap = min(12,max(0,snapshot.logical_processors - 4))
        if (gpu_mib + occupied_gpu > budget or cpu_workers + occupied_cpu > cpu_cap
                or heavy_gpu and any(x.heavy_gpu for x in self._leases.values())):
            return None
        lease=ResourceLease(job_id,gpu_mib,cpu_workers,heavy_gpu)
        self._leases[job_id]=lease
        return lease

    def acquire_measured(self, job_id: str, gpu_mib: int, cpu_workers: int,
                         heavy_gpu: bool, *, telemetry, device_id: str,
                         now: datetime) -> ResourceLease | None:
        """Admit against a *fresh*, validated host sample; never extrapolate missing telemetry.

        Telemetry is obtained by an explicitly approved G0 adapter. Reservations
        are in memory only and are NOT cross-process or crash-safe.
        """
        try:
            if not device_id or telemetry.device_id != device_id:
                return None
            observed = telemetry.observed_at
            if (not isinstance(now, datetime) or not isinstance(observed, datetime)
                    or not now.tzinfo or not observed.tzinfo):
                return None
            age = (now-observed).total_seconds()
            if not 0 <= age <= 10:
                return None
            c, g = telemetry.cpu_utilization_pct, telemetry.gpu_utilization_pct
            if (c is None or g is None or not all(math.isfinite(x) and 0 <= x <= 100 for x in (c, g))):
                return None
            total, free, processors = telemetry.vram_total_mib, telemetry.vram_free_mib, telemetry.logical_processors
            if (not all(type(x) is int for x in (total,free,processors))
                    or total <= 0 or free < 0 or free > total or processors <= 4
                    or not telemetry.gpu_name):
                return None
            if gpu_mib > 0 and heavy_gpu and g >= 90:
                return None
            # CPU headroom is a soft estimate, not a guarantee of physical core isolation.
            headroom = max(0, math.floor(processors * (100 - c) / 100))
            if cpu_workers + sum(x.cpu_workers for x in self._leases.values()) > headroom:
                return None
            return self.acquire(job_id, gpu_mib, cpu_workers, heavy_gpu,
                                ResourceSnapshot(total,free,processors))
        except (TypeError, ValueError, OverflowError, AttributeError):
            return None

    def release(self, job_id: str) -> None:
        self._leases.pop(job_id,None)


def retry_after_oom(model_id: str, retry_count: int) -> str:
    if retry_count == 0:
        return 'REDUCE_BATCH'
    if model_id == 'qwen3-vl:4b' and retry_count == 1:
        return 'FALLBACK_QWEN3_VL_2B'
    return 'BLOCKED_OOM'
