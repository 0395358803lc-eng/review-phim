"""Conservative, transactionally reserved CPU/GPU resource leases.

Exit verification is delegated to a trusted connector that MUST check both
PID and real OS process creation identity; a lone PID or boolean is never
proof of termination. This module does not start processes or inspect video.
"""
import math
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class ProcessStatus:
    device_id: str
    pid: int
    start_time_ns: int
    state: str


@dataclass(frozen=True)
class GpuLease:
    status: str
    device_id: str = ''
    job_id: str = ''
    gpu_mib: int = 0
    cpu_workers: int = 0
    heavy_gpu: bool = False
    pid: int | None = None
    process_started_ns: int | None = None


class DurableGpuLeaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with self._db() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('''CREATE TABLE IF NOT EXISTS gpu_leases (
                device_id TEXT NOT NULL, job_id TEXT NOT NULL,
                gpu_mib INTEGER NOT NULL, cpu_workers INTEGER NOT NULL,
                heavy_gpu INTEGER NOT NULL, status TEXT NOT NULL, pid INTEGER,
                process_started_ns INTEGER,
                PRIMARY KEY (device_id, job_id))''')
            # Safe forward migration: older prototypes have only the PID column.
            columns = {r[1] for r in con.execute('PRAGMA table_info(gpu_leases)')}
            if 'process_started_ns' not in columns:
                con.execute('ALTER TABLE gpu_leases ADD COLUMN process_started_ns INTEGER')

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
            row=con.execute('''SELECT status,device_id,job_id,gpu_mib,cpu_workers,
                               heavy_gpu,pid,process_started_ns
                               FROM gpu_leases WHERE device_id=? AND job_id=?''',
                            (device_id, job_id)).fetchone()
        return GpuLease(row[0],row[1],row[2],row[3],row[4],bool(row[5]),row[6],row[7]) if row else None

    def bind_pid(self, device_id: str, job_id: str, pid: int) -> bool:
        """Legacy API intentionally disabled: a PID alone can be reused by Windows."""
        return False

    def bind_process_identity(self, device_id: str, job_id: str, pid: int,
                              start_time_ns: int) -> bool:
        if (type(pid) is not int or pid <= 0 or pid >= 2**63
                or type(start_time_ns) is not int or not 0 < start_time_ns < 2**63):
            return False
        with self._db() as con:
            con.execute('BEGIN IMMEDIATE')
            count = con.execute('''UPDATE gpu_leases SET pid=?,process_started_ns=?
                                 WHERE device_id=? AND job_id=?
                                   AND status='RESERVED'
                                   AND pid IS NULL AND process_started_ns IS NULL''',
                                (pid,start_time_ns,device_id,job_id)).rowcount
        return count == 1

    def release(self, device_id: str, job_id: str,
                *, process_ended: Callable[[str,ProcessStatus],ProcessStatus] | None = None) -> GpuLease:
        with self._db() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('''SELECT pid,process_started_ns,status
                               FROM gpu_leases WHERE device_id=? AND job_id=?''',
                            (device_id,job_id)).fetchone()
            if (row is None or row[2] != 'RESERVED'
                    or type(row[0]) is not int or type(row[1]) is not int):
                return GpuLease('BLOCKED_UNRECONCILED')
            pid, start_time_ns, _ = row
            identity=ProcessStatus(device_id,pid,start_time_ns,'UNKNOWN')
            try:
                observed = process_ended(device_id,identity) if process_ended is not None else None
            except Exception:
                observed = None
            if (type(observed) is not ProcessStatus or
                    observed.device_id != device_id or observed.pid != pid or
                    observed.start_time_ns != start_time_ns or observed.state != 'EXITED'):
                return GpuLease('BLOCKED_UNRECONCILED')
            changed = con.execute('''UPDATE gpu_leases SET status='RELEASED'
                                     WHERE device_id=? AND job_id=? AND status='RESERVED'
                                       AND pid=? AND process_started_ns=?''',
                                  (device_id,job_id,pid,start_time_ns)).rowcount
            if changed != 1:
                return GpuLease('BLOCKED_UNRECONCILED')
        return GpuLease('RELEASED',device_id,job_id,pid=pid,process_started_ns=start_time_ns)
