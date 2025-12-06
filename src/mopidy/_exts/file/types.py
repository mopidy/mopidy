from __future__ import annotations

from typing import TypedDict


class FileConfig(TypedDict):
    media_dirs: list[str]
    excluded_file_extensions: list[str]
    show_dotfiles: bool
    follow_symlinks: bool
    metadata_timeout: int
