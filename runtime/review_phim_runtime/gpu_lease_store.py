"""Conservative SQLite cross-process GPU lease ledger; synthetic admission layer.

No lease is silently expired or released after a crash. A trusted connector
must reconcile the real PID before a resource claim can be released. This is
NOT a service or a permission to execute code on the user's machine.
"""
import math
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class GpuLease:
    status: str
    device_id: str = ''
    job_id: str = ''
    gpu_mib: int = 0
    cpu_workers: int = 0
    heavy_gpu: bool = False
    pid: int | None = None


class DurableGpuLeaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with self._db() as con:
            con.execute('''CREATE TABLE IF NOT EXISTS gpu_leases (
                device_id TEXT NOT NULL, job_id TEXT NOT NULL,
                gpu_mib INTEGER NOT NULL, cpu_workers INTEGER NOT NULL,
                heavy_gpu INTEGER NOT NULL, status TEXT NOT NULL, pid INTEGER,
                PRIMARY KEY (device_id, job_id))''')

    @contextmanager
    def _db(self):
        con = sqlite3.connect(self.db_path, timeout=30)
        try:
            con.execute('PRAGMA busy_timeout=30000')
            con.execute('PRAGMA synchronous=FULL')
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def claim(self, *, job_id: str, device_id: str, gpu_mib: int, cpu_workers: int,
              heavy_gpu: bool, telemetry, now: datetime) -> GpuLease:
        if (not isinstance(job_id, str) or not job_id.strip()
                or not isinstance(device_id, str) or not device_id.strip()
                or type(gpu_mib) is not int or gpu_mib < 0
                or type(cpu_workers) is not int or cpu_workers < 0
                or type(heavy_gpu) is not bool):
            return GpuLease('BLOCKED_RESOURCE_REQUEST')
        try:
            if (telemetry.device_id != device_id
                    or not isinstance(now, datetime) or not isinstance(telemetry.observed_at, datetime)
                    or not now.tzinfo or not telemetry.observed_at.tzinfo):
                return GpuLease('BLOCKED_TELEMETRY')
            age = (now - telemetry.observed_at).total_seconds()
            values = (telemetry.vram_total_mib, telemetry.vram_free_mib,
                      telemetry.logical_processors)
            loads = (telemetry.cpu_utilization_pct, telemetry.gpu_utilization_pct)
            if (not 0 <= age <= 10
                    or any(type(x) is not int for x in values)
                    or values[0] <= 0 or not 0 <= values[1] <= values[0]
                    or values[2] <= 4 or not telemetry.gpu_name
                    or any(not isinstance(x, (int, float)) or not math.isfinite(x)
                           or not 0 <= x <= 100 for x in loads)):
                return GpuLease('BLOCKED_TELEMETRY')
        except (AttributeError, OverflowError, ValueError, TypeError):
            return GpuLease('BLOCKED_TELEMETRY')
        if heavy_gpu and gpu_mib and telemetry.gpu_utilization_pct >= 90:
            return GpuLease('BLOCKED_GPU_BUSY')
        budget = max(0, min(math.floor(.75 * values[0]), values[1] - 1024))
        cpu_cap = min(12, max(0, values[2] - 4),
                      max(0, math.floor(values[2] * (100 - telemetry.cpu_utilization_pct) / 100)))
        with self._db() as con:
            con.execute('BEGIN IMMEDIATE')
            if con.execute('SELECT 1 FROM gpu_leases WHERE device_id=? AND job_id=?',
                           (device_id, job_id)).fetchone():
                return GpuLease('BLOCKED_DUPLICATE')
            row = con.execute('''SELECT COALESCE(SUM(gpu_mib),0),
                        COALESCE(SUM(cpu_workers),0),COALESCE(SUM(heavy_gpu),0)
                        FROM gpu_leases WHERE device_id=? AND status='RESERVED' ''',
                        (device_id,)).fetchone()
            used_gpu, used_cpu, heavy_count = row
            if heavy_gpu and heavy_count > 0:
                return GpuLease('BLOCKED_GPU_BUSY')
            if gpu_mib > budget - used_gpu:
                return GpuLease('BLOCKED_GPU_BUDGET')
            if cpu_workers > cpu_cap - used_cpu:
                return GpuLease('BLOCKED_CPU_BUDGET')
            con.execute('''INSERT INTO gpu_leases
                           (device_id,job_id,gpu_mib,cpu_workers,heavy_gpu,status)
                           VALUES (?,?,?,?,?,'RESERVED')''',
                        (device_id,job_id,gpu_mib,cpu_workers,int(heavy_gpu)))
        return GpuLease('RESERVED',device_id,job_id,gpu_mib,cpu_workers,heavy_gpu)

    def get(self, device_id: str, job_id: str) -> GpuLease | None:
        with self._db() as con:
            row=con.execute('''SELECT status,device_id,job_id,gpu_mib,cpu_workers,heavy_gpu,pid
                               FROM gpu_leases WHERE device_id=? AND job_id=?''',
                            (device_id, job_id)).fetchone()
        return GpuLease(row[0],row[1],row[2],row[3],row[4],bool(row[5]),row[6]) if row else None

    def bind_pid(self, device_id: str, job_id: str, pid: int) -> bool:
        if type(pid) is not int or pid <= 0:
            return False
        with self._db() as con:
            con.execute('BEGIN IMMEDIATE')
            count=con.execute('''UPDATE gpu_leases SET pid=?
                                 WHERE device_id=? AND job_id=? AND status='RESERVED' AND pid IS NULL''',
                              (pid,device_id,job_id)).rowcount
        return count == 1

    def release(self, device_id: str, job_id: str,
                *, process_ended: Callable[[str,int],bool] | None = None) -> GpuLease:
        with self._db() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('''SELECT pid,status FROM gpu_leases WHERE device_id=? AND job_id=?''',
                            (device_id,job_id)).fetchone()
            if row is None or row[1] != 'RESERVED' or type(row[0]) is not int:
                return GpuLease('BLOCKED_UNRECONCILED')
            try:
                ended = process_ended is not None and process_ended(device_id,row[0]) is True
            except Exception:
                ended = False
            if not ended:
                return GpuLease('BLOCKED_UNRECONCILED')
            con.execute('''UPDATE gpu_leases SET status='RELEASED'
                           WHERE device_id=? AND job_id=? AND status='RESERVED' ''',
                        (device_id,job_id))
        return GpuLease('RELEASED',device_id,job_id,pid=row[0])
