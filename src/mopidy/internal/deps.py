from __future__ import annotations

import platform
import re
import sys
from dataclasses import dataclass, field
from importlib import metadata
from os import PathLike
from pathlib import Path

from mopidy.internal import formatting
from mopidy.internal.gi import Gst, gi


@dataclass
class DepInfo:
    name: str
    version: str | None = None
    path: PathLike[str] | None = None
    dependencies: list[DepInfo] = field(default_factory=list)
    other: str | None = None


def format_dependency_list(dependencies: list[DepInfo] | None = None) -> str:
    if dependencies is None:
        seen_pkgs = set()
        ext_pkg_names = {
            ext_pkg_name
            for ep in metadata.entry_points(group="mopidy.ext")
            if ep.dist is not None
            and (ext_pkg_name := ep.dist.name.lower())
            and ext_pkg_name != "mopidy"
        }
        dependencies = [
            executable_info(),
            platform_info(),
            python_info(),
            pkg_info(
                pkg_name="mopidy",
                seen_pkgs=seen_pkgs,
            ),
            *[
                pkg_info(
                    pkg_name=pkg_name,
                    seen_pkgs=seen_pkgs,
                )
                for pkg_name in ext_pkg_names
            ],
            gstreamer_info(),
        ]
    return "\n".join(_format_dependency(dep) for dep in dependencies)


def _format_dependency(dep: DepInfo) -> str:
    lines = []

    if dep.version is None:
        lines.append(f"{dep.name}: not found")
    else:
        source = f" from {dep.path}" if dep.path else ""
        lines.append(f"{dep.name}: {dep.version}{source}")

    if dep.other:
        details = formatting.indent(dep.other, places=4)
        lines.append(f"  Detailed information: {details}")

    for sub_dep in dep.dependencies:
        sub_dep_lines = _format_dependency(sub_dep)
        lines.append(formatting.indent(sub_dep_lines, places=2, singles=True))

    return "\n".join(lines)


def executable_info() -> DepInfo:
    return DepInfo(
        name="Executable",
        version=sys.argv[0],
    )


def platform_info() -> DepInfo:
    return DepInfo(
        name="Platform",
        version=platform.platform(),
    )


def python_info() -> DepInfo:
    return DepInfo(
        name="Python",
        version=f"{platform.python_implementation()} {platform.python_version()}",
        path=Path(platform.__file__).parent,
    )


def pkg_info(
    *,
    pkg_name: str,
    depth: int = 0,
    seen_pkgs: set[str],
) -> DepInfo:
    try:
        dependencies = []
        distribution = metadata.distribution(pkg_name)
        if distribution.requires:
            for raw in distribution.requires:
                if "extra" in raw:
                    continue
                if match := re.match("[a-zA-Z0-9_-]+", raw):
                    name = match.group(0).lower()
                    if depth > 0 and name in seen_pkgs:
                        continue
                    seen_pkgs.add(name)
                    dependencies.append(
                        pkg_info(
                            pkg_name=name,
                            depth=depth + 1,
                            seen_pkgs=seen_pkgs,
                        ),
                    )
        return DepInfo(
            name=pkg_name,
            version=distribution.version,
            path=distribution.locate_file("."),  # pyright: ignore[reportArgumentType]
            dependencies=dependencies,
        )
    except metadata.PackageNotFoundError:
        return DepInfo(
            name=pkg_name,
        )


def gstreamer_info() -> DepInfo:
    other: list[str] = []
    other.append(f"Python wrapper: python-gi {gi.__version__}")

    found_elements = []
    missing_elements = []
    for name, version in _gstreamer_check_elements():
        if version:
            found_elements.append((name, version))
        else:
            missing_elements.append(name)

    other.append("Relevant elements:")
    other.append("  Found:")
    other.extend(f"    {element}: {version}" for (element, version) in found_elements)
    if not found_elements:
        other.append("    none")
    other.append("  Not found:")
    other.extend(f"    {element}" for element in missing_elements)
    if not missing_elements:
        other.append("    none")

    return DepInfo(
        name="GStreamer",
        version=".".join(map(str, Gst.version())),
        path=Path(gi.__file__).parent,
        other="\n".join(other),
    )


def _gstreamer_check_elements():
    elements_to_check = [
        # Core playback
        "uridecodebin",
        # External HTTP streams
        "souphttpsrc",
        # Spotify
        "spotifyaudiosrc",
        # Audio sinks
        "alsasink",
        "osssink",
        "oss4sink",
        "pulsesink",
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
        # Ogg Vorbis encoding and decoding
        "vorbisdec",
        "vorbisenc",
        "vorbisparse",
        "oggdemux",
        "oggmux",
        "oggparse",
        # Flac decoding
        "flacdec",
        "flacparse",
        # Shoutcast output
        "shout2send",
    ]

    def get_version(factory: Gst.PluginFeature):
        if plugin := factory.get_plugin():
            return plugin.get_version()
        return "unknown"

    known_elements = {
        factory.get_name(): get_version(factory)
        for factory in Gst.Registry.get().get_feature_list(Gst.ElementFactory)
    }
    return [(element, known_elements.get(element)) for element in elements_to_check]
