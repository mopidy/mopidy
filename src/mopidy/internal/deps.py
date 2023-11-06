from __future__ import annotations

import functools
import platform
import re
import sys
from collections.abc import Callable
from importlib import metadata
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from mopidy.internal import formatting
from mopidy.internal.gi import Gst, gi

if TYPE_CHECKING:
    from typing import TypeAlias

    class DepInfo(TypedDict, total=False):
        name: str
        version: str
        path: PathLike[str]
        dependencies: list[DepInfo]
        other: str

    Adapter: TypeAlias = Callable[[], DepInfo]


def format_dependency_list(adapters: list[Adapter] | None = None) -> str:
    if adapters is None:
        dist_names = {
            ep.dist.name
            for ep in metadata.entry_points(group="mopidy.ext")
            if ep.dist is not None and ep.dist.name != "Mopidy"
        }
        dist_infos = [
            functools.partial(pkg_info, dist_name) for dist_name in dist_names
        ]

        adapters = [
            executable_info,
            platform_info,
            python_info,
            functools.partial(pkg_info, "Mopidy", True),
            *dist_infos,
            gstreamer_info,
        ]
    return "\n".join(_format_dependency(a()) for a in adapters)


def _format_dependency(dep_info: DepInfo) -> str:
    lines = []

    if not (name := dep_info.get("name")):
        return "Name not found"

    if "version" not in dep_info:
        lines.append(f"{name}: not found")
    else:
        source = f" from {dep_info['path']}" if "path" in dep_info else ""
        lines.append(f"{name}: {dep_info['version']}{source}")

    if "other" in dep_info:
        details = formatting.indent(dep_info["other"], places=4)
        lines.append(f"  Detailed information: {details}")

    if dep_info.get("dependencies", []):
        for sub_dep_info in dep_info.get("dependencies", {}):
            sub_dep_lines = _format_dependency(sub_dep_info)
            lines.append(formatting.indent(sub_dep_lines, places=2, singles=True))

    return "\n".join(lines)


def executable_info() -> DepInfo:
    return {
        "name": "Executable",
        "version": sys.argv[0],
    }


def platform_info() -> DepInfo:
    return {
        "name": "Platform",
        "version": platform.platform(),
    }


def python_info() -> DepInfo:
    return {
        "name": "Python",
        "version": (f"{platform.python_implementation()} {platform.python_version()}"),
        "path": Path(platform.__file__).parent,
    }


def pkg_info(
    project_name: str | None = None,
    include_transitive_deps: bool = True,
    include_extras: bool = False,
) -> DepInfo:
    if project_name is None:
        project_name = "Mopidy"
    try:
        distribution = metadata.distribution(project_name)
        if include_transitive_deps and distribution.requires:
            dependencies = []
            for raw in distribution.requires:
                if "importlib_metadata" in raw or (
                    not include_extras and "extra" in raw
                ):
                    continue
                if match := re.match("[a-zA-Z0-9_-]+", raw):
                    entry = match.group(0)
                    dependencies.append(
                        pkg_info(
                            entry,
                            include_transitive_deps=entry != "Mopidy",
                        )
                    )
        else:
            dependencies = []
        return {
            "name": project_name,
            "version": distribution.version,
            "path": distribution.locate_file("."),
            "dependencies": dependencies,
        }
    except metadata.PackageNotFoundError:
        return {
            "name": project_name,
        }


def gstreamer_info() -> DepInfo:
    other: list[str] = []
    other.append(f"Python wrapper: python-gi {gi.__version__}")

    found_elements = []
    missing_elements = []
    for name, status in _gstreamer_check_elements():
        if status:
            found_elements.append(name)
        else:
            missing_elements.append(name)

    other.append("Relevant elements:")
    other.append("  Found:")
    for element in found_elements:
        other.append(f"    {element}")
    if not found_elements:
        other.append("    none")
    other.append("  Not found:")
    for element in missing_elements:
        other.append(f"    {element}")
    if not missing_elements:
        other.append("    none")

    return {
        "name": "GStreamer",
        "version": ".".join(map(str, Gst.version())),
        "path": Path(gi.__file__).parent,
        "other": "\n".join(other),
    }


def _gstreamer_check_elements():
    elements_to_check = [
        # Core playback
        "uridecodebin",
        # External HTTP streams
        "souphttpsrc",
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
    known_elements = [
        factory.get_name()
        for factory in Gst.Registry.get().get_feature_list(Gst.ElementFactory)
    ]
    return [(element, element in known_elements) for element in elements_to_check]
