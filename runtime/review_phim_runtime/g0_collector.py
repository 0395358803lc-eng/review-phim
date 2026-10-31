"""Hardware-first G0 inventory from fixed read-only commands, never film content.

Only a separately authorized, device-bound host adapter may provide runner.
This is not a host daemon, install or PROCESS_APPROVED. All tool presence
observations remain untested, including GPU backend and NVENC support.
"""
from dataclasses import dataclass
from typing import Callable, Mapping
import json
from .telemetry import parse_nvidia_csv

# No user data is interpolated; no drive/folder traversal, video decoding or file writes.
G0_POWERSHELL_SCRIPT = r'''$ErrorActionPreference='Stop'
$os=Get-CimInstance Win32_OperatingSystem
$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1
$cs=Get-CimInstance Win32_ComputerSystem
$drives=@(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
    @{device=$_.DeviceID;total_bytes=[int64]$_.Size;free_bytes=[int64]$_.FreeSpace}
})
$tools=@('python','node','ffmpeg','ffprobe','nvidia-smi','ollama','git') | ForEach-Object {
    $item=Get-Command $_ -ErrorAction SilentlyContinue | Select-Object -First 1
    if($item -and $item.Source) { @{name=$_.ToString();path=$item.Source.ToString()} }
}
@{os=@{name=$os.Caption;version=$os.Version;architecture=$os.OSArchitecture};
  cpu=@{name=$cpu.Name;cores=[int]$cpu.NumberOfCores;logical_processors=[int]$cpu.NumberOfLogicalProcessors};
  ram_bytes=[int64]$cs.TotalPhysicalMemory;drives=$drives;tools=@($tools)} |
  ConvertTo-Json -Depth 5 -Compress
'''
G0_POWERSHELL_ARGV = ('powershell.exe', '-NoProfile', '-NonInteractive', '-Command', G0_POWERSHELL_SCRIPT)
G0_NVIDIA_ARGV = (
    'nvidia-smi',
    '--query-gpu=name,memory.total,memory.free,driver_version,utilization.gpu',
    '--format=csv,noheader,nounits'
)


@dataclass(frozen=True)
class DriveInfo:
    device: str
    total_bytes: int
    free_bytes: int


@dataclass(frozen=True)
class G0Snapshot:
    device_id: str
    os_name: str
    os_version: str
    architecture: str
    cpu_name: str
    cpu_cores: int
    cpu_logical: int
    ram_bytes: int
    drives: tuple[DriveInfo, ...]
    tool_paths: Mapping[str, str]
    gpu_name: str | None = None
    vram_total_mib: int | None = None
    vram_free_mib: int | None = None
    gpu_driver: str | None = None
    cuda_runtime_tested: bool | None = None


@dataclass(frozen=True)
class G0Result:
    status: str
    snapshot: G0Snapshot | None = None


def _positive_int(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError('Expected positive integer')
    return value


def _nonnegative_int(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError('Expected non-negative integer')
    return value


def _label(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing text field')
    return value.strip()


def _decode_os_observation(device_id: str, raw: str) -> G0Snapshot:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('G0 result must be object')
    os_info, cpu = data['os'], data['cpu']
    if not isinstance(os_info,dict) or not isinstance(cpu,dict):
        raise ValueError('Invalid OS or CPU fields')
    drives = data['drives']
    tools = data['tools']
    if not isinstance(drives, list) or not isinstance(tools, list):
        raise ValueError('Drives/tools must be arrays')
    parsed_drives = []
    for drive in drives:
        name = _label(drive['device'])
        if len(name) != 2 or not name[0].isalpha() or name[1] != ':':
            raise ValueError('Invalid local disk')
        total, free = _positive_int(drive['total_bytes']), _nonnegative_int(drive['free_bytes'])
        if free > total:
            raise ValueError('Free disk space exceeds total')
        parsed_drives.append(DriveInfo(name, total, free))
    paths: dict[str,str] = {}
    for tool in tools:
        name, path = _label(tool['name']), _label(tool['path'])
        if name in paths:
            raise ValueError('Duplicate tool')
        paths[name] = path
    return G0Snapshot(device_id, _label(os_info['name']), _label(os_info['version']),
                      _label(os_info['architecture']), _label(cpu['name']),
                      _positive_int(cpu['cores']), _positive_int(cpu['logical_processors']),
                      _positive_int(data['ram_bytes']),tuple(parsed_drives),paths)


def collect_g0(device_id: str, runner: Callable, *, approved: bool) -> G0Result:
    """Return G0_OBSERVED (not INSTALLED_USABLE); never use this to probe media."""
    if approved is not True:
        return G0Result('BLOCKED_G0_APPROVAL')
    if not isinstance(device_id,str) or not device_id.strip():
        return G0Result('BLOCKED_DEVICE')
    try:
        raw = runner(G0_POWERSHELL_ARGV)
        if raw['returncode'] != 0:
            return G0Result('BLOCKED_G0_INVALID')
        snapshot = _decode_os_observation(device_id.strip(), raw['stdout'])
    except (KeyError, TypeError, ValueError, OSError, RuntimeError, json.JSONDecodeError):
        return G0Result('BLOCKED_G0_INVALID')
    try:
        raw_gpu = runner(G0_NVIDIA_ARGV)
        if raw_gpu['returncode'] != 0:
            return G0Result('G0_PARTIAL', snapshot)
        gpu = parse_nvidia_csv(raw_gpu['stdout'])
    except (KeyError, TypeError, ValueError, OSError, RuntimeError):
        return G0Result('G0_PARTIAL', snapshot)
    from dataclasses import replace
    return G0Result('G0_OBSERVED',replace(snapshot,gpu_name=gpu.name,
             vram_total_mib=gpu.total_mib,vram_free_mib=gpu.free_mib,gpu_driver=gpu.driver_version))


def to_host_inventory(observation: G0Result):
    """Bridge G0 metadata to registry without promoting presence into TESTED_LOCAL.

    An incomplete GPU inventory is not enough to assign a VRAM figure.
    """
    from .contracts import Capability, HostInventory
    snap = observation.snapshot
    if snap is None or snap.vram_total_mib is None:
        return None
    caps = {key:Capability(name=key,version='',path=path,tested=False)
            for key,path in snap.tool_paths.items()}
    return HostInventory(snap.device_id,snap.os_name,snap.vram_total_mib,caps)
