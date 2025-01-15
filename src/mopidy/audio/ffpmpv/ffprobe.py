import json
import subprocess
from typing import Any

from mopidy.internal.path import path_from_file_uri

# TODO: Completely guesswork really
ffprobe_format_name_to_mime = {
    "aac": "audio/aac",
    "aiff": "audio/aiff",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
    "opus": "audio/ogg",
    "wav": "audio/wav",
    "wma": "audio/x-ms-wma",
}


def run_ffprobe(uri: str, timeout: float | None = None) -> dict[str, Any]:
    args = [
        "ffprobe",
        "-hide_banner",
        "-of",
        "json",
        "-show_format",
        str(path_from_file_uri(uri)),
    ]
    output = subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=timeout)  # noqa: S603
    return json.loads(output)
