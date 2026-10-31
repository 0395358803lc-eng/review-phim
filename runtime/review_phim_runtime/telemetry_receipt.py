"""G0 telemetry receipt stamped at completion with a trusted host clock.

Wall-clock stamps alone are insufficient: monotonic elapsed time detects
slow/rolled-back samples. Clock and runner come from a trusted connector.
"""
from dataclasses import dataclass, is_dataclass, replace
from datetime import datetime
from typing import Callable
import math
from .g0_security import G0ReadGrant, validate_g0_read_scope


@dataclass(frozen=True)
class TelemetryReceipt:
    status: str
    sample: object | None = None


def read_bound_telemetry(device_id: str, grant: G0ReadGrant, device_runner,
                         verifier: Callable, *, now: datetime, logical_processors: int,
                         monotonic: Callable[[], float], utcnow: Callable[[], datetime],
                         collector=None, max_sample_seconds: float = 5.0) -> TelemetryReceipt:
    """Measure start/end and stamp successful reading at completion.

    Callers must supply authentic host monotonic and UTC clocks; passing
    arbitrary clocks is only appropriate for synthetic unit tests.
    """
    status = validate_g0_read_scope(device_id,grant,device_runner,verifier,
                                    now=now,operation='G0_TELEMETRY')
    if status != 'ALLOW':
        return TelemetryReceipt(status)
    if type(logical_processors) is not int or logical_processors <= 0:
        return TelemetryReceipt('BLOCKED_TELEMETRY_INPUT')
    if collector is None:
        from .telemetry import collect_telemetry
        collector = collect_telemetry
    try:
        tick_start, wall_start = float(monotonic()), utcnow()
        if not isinstance(wall_start,datetime) or not wall_start.tzinfo:
            return TelemetryReceipt('BLOCKED_TELEMETRY_CLOCK')
        sample = collector(device_id,device_runner,approved=True,
                           now=wall_start,logical_processors=logical_processors)
        tick_end, wall_end = float(monotonic()), utcnow()
        if (not all(map(math.isfinite,(tick_start,tick_end))) or tick_end < tick_start
                or not isinstance(wall_end,datetime) or wall_end < wall_start
                or not wall_end.tzinfo):
            return TelemetryReceipt('BLOCKED_TELEMETRY_CLOCK')
        if tick_end-tick_start > max_sample_seconds or wall_end >= grant.expires_at:
            return TelemetryReceipt('BLOCKED_TELEMETRY_SLOW')
        if sample is None:
            return TelemetryReceipt('BLOCKED_TELEMETRY_INVALID')
        if isinstance(sample,dict):
            sample={**sample,'observed_at':wall_end}
        elif is_dataclass(sample):
            sample=replace(sample,observed_at=wall_end)
        else:
            return TelemetryReceipt('BLOCKED_TELEMETRY_INVALID')
        return TelemetryReceipt('G0_TELEMETRY_OBSERVED',sample)
    except (TypeError,ValueError,OverflowError,OSError,RuntimeError,AttributeError):
        return TelemetryReceipt('BLOCKED_TELEMETRY_INVALID')
