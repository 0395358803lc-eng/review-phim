"""In-memory admission prototype; not persistent and not a host daemon."""
from dataclasses import dataclass
import math


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

    def release(self, job_id: str) -> None:
        self._leases.pop(job_id,None)


def retry_after_oom(model_id: str, retry_count: int) -> str:
    if retry_count == 0:
        return 'REDUCE_BATCH'
    if model_id == 'qwen3-vl:4b' and retry_count == 1:
        return 'FALLBACK_QWEN3_VL_2B'
    return 'BLOCKED_OOM'
