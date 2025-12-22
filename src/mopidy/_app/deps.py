from __future__ import annotations

import argparse
import platform
import re
import sys
from dataclasses import dataclass, field
from importlib import metadata
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from mopidy.commands import Command
from mopidy.internal.gi import Gst

if TYPE_CHECKING:
    from mopidy.config import Config


class DepsCommand(Command):
    help = "Show dependencies and debug information."

    def __init__(self) -> None:
        super().__init__()
        self.set(base_verbosity_level=-1)

    @override
    def run(
        self,
        args: argparse.Namespace,
        config: Config,
        *_args: Any,
        **_kwargs: Any,
    ) -> int:
        print("\n".join(dep.format() for dep in get_dependencies()))  # noqa: T201
        return 0


@dataclass
class Dependency:
    name: str
    version: str | None = None
    path: PathLike[str] | None = None
    dependencies: list[Dependency] = field(default_factory=list)
    other: str | None = None

    def format(self) -> str:
        return "\n".join(
            [
                (
                    (
                        f"{self.name}: {self.version}"
                        + (f" from {self.path}" if self.path else "")
                    )
                    if self.version
                    else f"{self.name}: not found"
                ),
                *(
                    (" " * 2 + line for line in self.other.splitlines())
                    if self.other
                    else []
                ),
                *(
                    " " * 2 + line
                    for dep in self.dependencies
                    for line in dep.format().splitlines()
                ),
            ]
        )


def get_dependencies() -> list[Dependency]:
    seen_pkg_names = set[str]()
    extension_pkg_names = sorted(
        {
            python_pkg_name
            for entry_point in metadata.entry_points(group="mopidy.ext")
            if entry_point.dist is not None
            and (python_pkg_name := entry_point.dist.name.lower())
            and python_pkg_name != "mopidy"
        }
    )
    return [
        Dependency(
            name="Executable",
            version=sys.argv[0],
        ),
        Dependency(
            name="Platform",
            version=platform.platform(),
        ),
        Dependency(
            name="Python",
            version=f"{platform.python_implementation()} {platform.python_version()}",
            path=Path(platform.__file__).parent if platform.__file__ else None,
        ),
        python_pkg(
            pkg_name="mopidy",
            seen_pkg_names=seen_pkg_names,
        ),
        *[
            python_pkg(
                pkg_name=pkg_name,
                seen_pkg_names=seen_pkg_names,
            )
            for pkg_name in extension_pkg_names
        ],
        Dependency(
            name="GStreamer",
            version=".".join(map(str, Gst.version())),
            other=gstreamer_info(),
        ),
    ]


def python_pkg(
    *,
    pkg_name: str,
    depth: int = 0,
    seen_pkg_names: set[str],
) -> Dependency:
    try:
        dependencies = []
        distribution = metadata.distribution(pkg_name)
        if distribution.requires:
            for raw in distribution.requires:
                if "extra" in raw:
                    continue
                if match := re.match("[a-zA-Z0-9_-]+", raw):
                    name = match.group(0).lower()
                    if depth > 0 and name in seen_pkg_names:
                        continue
                    seen_pkg_names.add(name)
                    dependencies.append(
                        python_pkg(
                            pkg_name=name,
                            depth=depth + 1,
                            seen_pkg_names=seen_pkg_names,
                        ),
                    )
        return Dependency(
            name=pkg_name,
            version=distribution.version,
            path=Path(str(distribution.locate_file("."))),
            dependencies=dependencies,
        )
    except metadata.PackageNotFoundError:
        return Dependency(
            name=pkg_name,
        )


def gstreamer_info() -> str:
    elements_to_check = [
        # Core playback
        "uridecodebin",
        #
        # External HTTP streams
        "souphttpsrc",
        #
        # Spotify
        "spotifyaudiosrc",
        #
        # Audio sinks
        "alsasink",
        "osssink",
        "oss4sink",
        "pulsesink",
        #
        # MP3 encoding and decoding
        #
        # One of flump3dec, mad, and mpg123audiodec is required for MP3
        # playback.
        "flump3dec",
        "id3demux",
        "id3v2mux",
        "lamemp3enc",
        "mad",
        "mpegaudioparse",
        "mpg123audiodec",
        #
        # Ogg Vorbis encoding and decoding
        "vorbisdec",
        "vorbisenc",
        "vorbisparse",
        "oggdemux",
        "oggmux",
        "oggparse",
        #
        # Flac decoding
        "flacdec",
        "flacparse",
        #
        # Shoutcast output
        "shout2send",
    ]

    all_known_elements = {
        factory.get_name(): plugin.get_version()
        for factory in Gst.Registry.get().get_feature_list(Gst.ElementFactory)
        if (plugin := factory.get_plugin())
    }
    found_elements = [
        (element, version)
        for element in elements_to_check
        if (version := all_known_elements.get(element))
    ]
    missing_elements = [
        element for element in elements_to_check if element not in all_known_elements
    ]

    return "\n".join(
        [
            "Available elements:",
            *(f"  {element}: {version}" for (element, version) in found_elements),
            *(["  none"] if not found_elements else []),
            "Missing elements:",
            *(f"  {element}" for element in missing_elements),
            *(["  none"] if not missing_elements else []),
        ]
    )
