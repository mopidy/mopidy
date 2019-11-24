import platform
import sys
import unittest
from unittest import mock

import pkg_resources

from mopidy.internal import deps
from mopidy.internal.gi import Gst, gi


class DepsTest(unittest.TestCase):
    def test_format_dependency_list(self):
        adapters = [
            lambda: dict(name="Python", version="FooPython 2.7.3"),
            lambda: dict(name="Platform", version="Loonix 4.0.1"),
            lambda: dict(
                name="Pykka", version="1.1", path="/foo/bar", other="Quux"
            ),
            lambda: dict(name="Foo"),
            lambda: dict(
                name="Mopidy",
                version="0.13",
                dependencies=[
                    dict(
                        name="pylast",
                        version="0.5",
                        dependencies=[dict(name="setuptools", version="0.6")],
                    )
                ],
            ),
        ]

        result = deps.format_dependency_list(adapters)

        assert "Python: FooPython 2.7.3" in result

        assert "Platform: Loonix 4.0.1" in result

        assert "Pykka: 1.1 from /foo/bar" in result
        assert "/baz.py" not in result
        assert "Detailed information: Quux" in result

        assert "Foo: not found" in result

        assert "Mopidy: 0.13" in result
        assert "  pylast: 0.5" in result
        assert "    setuptools: 0.6" in result

    def test_executable_info(self):
        result = deps.executable_info()

        assert "Executable" == result["name"]
        assert sys.argv[0] in result["version"]

    def test_platform_info(self):
        result = deps.platform_info()

        assert "Platform" == result["name"]
        assert platform.platform() in result["version"]

    def test_python_info(self):
        result = deps.python_info()

        assert "Python" == result["name"]
        assert platform.python_implementation() in result["version"]
        assert platform.python_version() in result["version"]
        assert "python" in result["path"]
        assert "platform.py" not in result["path"]

    def test_gstreamer_info(self):
        result = deps.gstreamer_info()

        assert "GStreamer" == result["name"]
        assert ".".join(map(str, Gst.version())) == result["version"]
        assert "gi" in result["path"]
        assert "__init__.py" not in result["path"]
        assert "Python wrapper: python-gi" in result["other"]
        assert gi.__version__ in result["other"]
        assert "Relevant elements:" in result["other"]

    @mock.patch("pkg_resources.get_distribution")
    def test_pkg_info(self, get_distribution_mock):
        dist_setuptools = mock.Mock()
        dist_setuptools.project_name = "setuptools"
        dist_setuptools.version = "0.6"
        dist_setuptools.location = "/tmp/example/setuptools"
        dist_setuptools.requires.return_value = []

        dist_pykka = mock.Mock()
        dist_pykka.project_name = "Pykka"
        dist_pykka.version = "1.1"
        dist_pykka.location = "/tmp/example/pykka"
        dist_pykka.requires.return_value = [dist_setuptools]

        dist_mopidy = mock.Mock()
        dist_mopidy.project_name = "Mopidy"
        dist_mopidy.version = "0.13"
        dist_mopidy.location = "/tmp/example/mopidy"
        dist_mopidy.requires.return_value = [dist_pykka]

        get_distribution_mock.side_effect = [
            dist_mopidy,
            dist_pykka,
            dist_setuptools,
        ]

        result = deps.pkg_info()

        assert "Mopidy" == result["name"]
        assert "0.13" == result["version"]
        assert "mopidy" in result["path"]

        dep_info_pykka = result["dependencies"][0]
        assert "Pykka" == dep_info_pykka["name"]
        assert "1.1" == dep_info_pykka["version"]

        dep_info_setuptools = dep_info_pykka["dependencies"][0]
        assert "setuptools" == dep_info_setuptools["name"]
        assert "0.6" == dep_info_setuptools["version"]

    @mock.patch("pkg_resources.get_distribution")
    def test_pkg_info_for_missing_dist(self, get_distribution_mock):
        get_distribution_mock.side_effect = pkg_resources.DistributionNotFound

        result = deps.pkg_info()

        assert "Mopidy" == result["name"]
        assert "version" not in result
        assert "path" not in result

    @mock.patch("pkg_resources.get_distribution")
    def test_pkg_info_for_wrong_dist_version(self, get_distribution_mock):
        get_distribution_mock.side_effect = pkg_resources.VersionConflict

        result = deps.pkg_info()

        assert "Mopidy" == result["name"]
        assert "version" not in result
        assert "path" not in result
