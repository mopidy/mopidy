import platform
import sys
from importlib import metadata
from pathlib import Path

from pytest_mock import MockFixture

from mopidy._server import deps
from mopidy.internal.gi import Gst


def test_format_dependency_list():
    adapters = [
        deps.DepInfo(
            name="Python",
            version="FooPython 3.12.3",
        ),
        deps.DepInfo(
            name="Platform",
            version="Loonix 7.0.1",
        ),
        deps.DepInfo(
            name="pykka",
            version="5.1",
            path=Path("/foo/bar"),
            other="Quux",
        ),
        deps.DepInfo(
            name="foo",
        ),
        deps.DepInfo(
            name="mopidy",
            version="4.13",
            dependencies=[
                deps.DepInfo(
                    name="pylast",
                    version="0.5",
                ),
            ],
        ),
    ]

    result = deps.format_dependency_list(adapters)
    assert "Python: FooPython 3.12.3" in result
    assert "Platform: Loonix 7.0.1" in result
    assert "pykka: 5.1 from /foo/bar" in result
    assert "/baz.py" not in result
    assert "Detailed information:\n    Quux" in result
    assert "foo: not found" in result
    assert "mopidy: 4.13" in result
    assert "  pylast: 0.5" in result


def test_format_dependency_list_real():
    result = deps.format_dependency_list()
    assert "Python 3." in result
    assert "mopidy:" in result


def test_executable_info():
    result = deps.executable_info()

    assert result.name == "Executable"
    assert result.version
    assert sys.argv[0] in result.version


def test_platform_info():
    result = deps.platform_info()

    assert result.name == "Platform"
    assert result.version
    assert platform.platform() in result.version


def test_python_info():
    result = deps.python_info()

    assert result.name == "Python"
    assert result.version
    assert platform.python_implementation() in result.version
    assert platform.python_version() in result.version
    assert "python" in str(result.path)
    assert "platform.py" not in str(result.path)


def test_gstreamer_info():
    result = deps.gstreamer_info()

    assert result.name == "GStreamer"
    assert result.version
    assert ".".join(map(str, Gst.version())) == result.version
    assert "gi" in str(result.path)
    assert "__init__.py" not in str(result.path)
    assert result.other
    assert "Available elements:" in result.other


def test_gstreamer_check_elements(mocker: MockFixture):
    mocker.patch.object(
        deps,
        "_gstreamer_check_elements",
        return_val=("test1", True),
    )

    result = deps.gstreamer_info()

    assert result.other
    assert "  none" in result.other


def test_pkg_info(mocker: MockFixture):
    dist_setuptools = mocker.MagicMock()
    dist_setuptools.name = "setuptools"
    dist_setuptools.version = "0.6"
    dist_setuptools.locate_file = mocker.MagicMock(
        return_value=Path("/tmp/example/setuptools/main.py"),
    )
    dist_setuptools.requires = []

    dist_pykka = mocker.Mock()
    dist_pykka.name = "Pykka"
    dist_pykka.version = "1.1"
    dist_pykka.locate_file = mocker.MagicMock(
        return_value=Path("/tmp/example/pykka/main.py"),
    )
    dist_pykka.requires = [f"{dist_setuptools.name}==0.6"]

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
        dist_setuptools,
    ]

    mopidy_dep = deps.pkg_info(pkg_name="mopidy", seen_pkgs=set())

    assert mopidy_dep.name == "mopidy"
    assert mopidy_dep.version == "0.13"
    assert "mopidy" in str(mopidy_dep.path)

    pykka_dep = mopidy_dep.dependencies[0]
    assert pykka_dep.name == "pykka"
    assert pykka_dep.version == "1.1"

    setuptools_dep = pykka_dep.dependencies[0]
    assert setuptools_dep.name == "setuptools"
    assert setuptools_dep.version == "0.6"


def test_pkg_info_for_missing_dist(mocker: MockFixture):
    get_distribution_mock = mocker.patch.object(metadata, "distribution")
    get_distribution_mock.side_effect = metadata.PackageNotFoundError("test")

    result = deps.pkg_info(pkg_name="mopidy", seen_pkgs=set())

    assert result.name == "mopidy"
    assert result.version is None
    assert result.path is None


def test_pkg_info_real():
    result = deps.pkg_info(
        pkg_name="mopidy",
        seen_pkgs=set(),
    )
    assert result
