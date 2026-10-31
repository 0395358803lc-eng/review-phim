"""Pure contracts for an uninstalled, non-media runtime prototype."""
from dataclasses import dataclass
from typing import Mapping

NICHE_IDS = ('review', 'recap', 'review-recap', 'film-explained', 'character-theme')
STAGES = ('CONNECT_DEVICE', 'SELECT_SOURCE_FOLDER', 'SELECT_SOURCE_VIDEO',
          'SELECT_REVIEW_NICHE', 'G0', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7')


@dataclass(frozen=True)
class SourceInterval:
    start_s: float
    end_s: float

    def __post_init__(self):
        import math
        if not (math.isfinite(self.start_s) and math.isfinite(self.end_s)
                and self.start_s >= 0 and self.end_s > self.start_s):
            raise ValueError('Source intervals must be positive half-open ranges')


@dataclass(frozen=True)
class FactClaim:
    status: str
    direct_media_reviewed: bool = False

    def __post_init__(self):
        if self.status == 'VERIFIED' and not self.direct_media_reviewed:
            raise ValueError('A model report alone cannot verify film facts')


@dataclass(frozen=True)
class WorkItem:
    device_id: str
    job_id: str
    path: str
    operation: str
    interval: SourceInterval
    estimated_bytes: int
    idempotency_key: str


@dataclass(frozen=True)
class Capability:
    name: str
    version: str
    path: str
    tested: bool


@dataclass(frozen=True)
class HostInventory:
    device_id: str
    os_name: str
    total_vram_mib: int
    capabilities: Mapping[str, Capability]
