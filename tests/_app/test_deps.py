import platform
import sys
from importlib import metadata
from pathlib import Path

from pytest_mock import MockFixture

from mopidy._app import deps
from mopidy.internal.gi import Gst


def test_dependency_format():
    dependency = deps.Dependency(
        name="mopidy",
        version="4.13",
        dependencies=[
            deps.Dependency(
                name="pykka",
                version="5.1",
                path=Path("/foo/bar"),
                other="Quux",
            ),
        ],
    )

    result = dependency.format()

    assert result.splitlines() == [
        "mopidy: 4.13",
        "  pykka: 5.1 from /foo/bar",
        "    Quux",
    ]


def test_get_dependencies():
    result = {dep.name: dep for dep in deps.get_dependencies()}

    assert "Executable" in result
    assert result["Executable"].version == sys.argv[0]

    assert "Platform" in result
    assert result["Platform"].version == platform.platform()

    assert "Python" in result
    assert platform.python_implementation() in str(result["Python"].version)
    assert platform.python_version() in str(result["Python"].version)
    assert "python" in str(result["Python"].path)

    assert "mopidy" in result

    assert "GStreamer" in result
    assert ".".join(map(str, Gst.version())) in str(result["GStreamer"].version)


def test_python_pkg(mocker: MockFixture):
    dist_pykka = mocker.Mock()
    dist_pykka.name = "Pykka"
    dist_pykka.version = "1.1"
    dist_pykka.locate_file = mocker.MagicMock(
        return_value=Path("/tmp/example/pykka/main.py"),
    )
    dist_pykka.requires = []

    dist_mopidy = mocker.Mock()
    dist_mopidy.name = "Mopidy"
    dist_mopidy.version = "0.13"
    dist_mopidy.locate_file = mocker.MagicMock(
        return_value=Path("/tmp/example/mopidy/no_name.py"),
    )
    dist_mopidy.requires = [f"{dist_pykka.name}==1.1"]

    get_distribution_mock = mocker.patch.object(metadata, "distribution")
    get_distribution_mock.side_effect = [
        dist_mopidy,
        dist_pykka,
    ]

    mopidy_dep = deps.python_pkg(
        pkg_name="mopidy",
        seen_pkg_names=set(),
    )

    assert mopidy_dep.name == "mopidy"
    assert mopidy_dep.version == "0.13"
    assert "mopidy" in str(mopidy_dep.path)

    pykka_dep = mopidy_dep.dependencies[0]
    assert pykka_dep.name == "pykka"
    assert pykka_dep.version == "1.1"


def test_python_pkg_for_missing_dist(mocker: MockFixture):
    get_distribution_mock = mocker.patch.object(metadata, "distribution")
    get_distribution_mock.side_effect = metadata.PackageNotFoundError("test")

    result = deps.python_pkg(
        pkg_name="mopidy",
        seen_pkg_names=set(),
    )

    assert result.name == "mopidy"
    assert result.version is None
    assert result.path is None


def test_python_pkg_real():
    result = deps.python_pkg(
        pkg_name="mopidy",
        seen_pkg_names=set(),
    )
    assert result


def test_gstreamer_info():
    result = deps.gstreamer_info()

    assert "Available elements:" in result
    assert "Missing elements:" in result
