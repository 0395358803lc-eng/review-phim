"""G0 compatibility is never inferred from GPU name alone."""
from .contracts import HostInventory

REQUIRED = ('ffmpeg','ffprobe','scenedetect','asr_gpu','vlm_gpu','vad_cpu','tts_vi')


def resolve_capabilities(inventory: HostInventory, profile_id: str) -> dict[str,str]:
    if profile_id not in ('balanced','fast','quality'):
        raise ValueError('Unknown profile')
    result = {}
    for key in REQUIRED:
        observed = inventory.capabilities.get(key)
        if observed is None:
            result[key] = 'INSTALL_PROPOSED'
        elif not observed.version or not observed.path:
            result[key] = 'UNKNOWN'
        else:
            result[key] = 'INSTALLED_USABLE' if observed.tested else 'CONDITIONAL'
    return result
