from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, TypedDict


class M3UConfig(TypedDict):
    base_dir: Optional[Path]
    default_encoding: str
    default_extension: Literal[".m3u", ".m3u8"]
    playlists_dir: Optional[Path]
