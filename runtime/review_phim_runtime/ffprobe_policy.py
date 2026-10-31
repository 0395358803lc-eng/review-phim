"""Exact, no-output FFprobe argument grammar. Not a media permission grant."""
from .contracts import WorkItem


def build_ffprobe_argv(item: WorkItem) -> list[str]:
    if item.operation != 'PROBE':
        raise ValueError('Only a separately approved PROBE operation can use ffprobe')
    return ['-v', 'error', '-show_format', '-show_streams', '-of', 'json', item.path]


def validate_ffprobe_argv(tool: str, item: WorkItem, args: list[str]) -> bool:
    if tool != 'ffprobe' or item.operation != 'PROBE':
        return False
    return type(args) is list and args == build_ffprobe_argv(item)
