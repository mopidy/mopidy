import platform
import sys
from importlib import metadata
from pathlib import Path
from unittest import mock

import pytest
from mopidy.internal import deps
from mopidy.internal.gi import Gst, gi


class TestDeps:
    def test_format_dependency_list(self):
        adapters = [
            lambda: {
                "name": "Python",
                "version": "FooPython 2.7.3",
            },
            lambda: {
                "name": "Platform",
                "version": "Loonix 4.0.1",
            },
            lambda: {
                "name": "Pykka",
                "version": "1.1",
                "path": "/foo/bar",
                "other": "Quux",
            },
            lambda: {
                "name": "Foo",
            },
            lambda: {
                "name": "Mopidy",
                "version": "0.13",
                "dependencies": [
                    {
                        "name": "pylast",
                        "version": "0.5",
                        "dependencies": [{"name": "setuptools", "version": "0.6"}],
                    }
                ],
            },
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

    def test_format_dependency_list_real(self):
        result = deps.format_dependency_list()
        assert "Python 3." in result
        assert "Mopidy: 4." in result
        assert "setuptools: 6" in result

    def test_executable_info(self):
        result = deps.executable_info()

        assert result["name"] == "Executable"
        assert sys.argv[0] in result["version"]

    def test_platform_info(self):
        result = deps.platform_info()

        assert result["name"] == "Platform"
        assert platform.platform() in result["version"]

    def test_python_info(self):
        result = deps.python_info()

        assert result["name"] == "Python"
        assert platform.python_implementation() in result["version"]
        assert platform.python_version() in result["version"]
        assert "python" in str(result["path"])
        assert "platform.py" not in str(result["path"])

    def test_gstreamer_info(self):
        result = deps.gstreamer_info()

        assert result["name"] == "GStreamer"
        assert ".".join(map(str, Gst.version())) == result["version"]
        assert "gi" in str(result["path"])
        assert "__init__.py" not in str(result["path"])
        assert "Python wrapper: python-gi" in result["other"]
        assert gi.__version__ in result["other"]
        assert "Relevant elements:" in result["other"]

    def test_gstreamer_check_elements(self):
        with mock.patch(
            "mopidy.internal.deps._gstreamer_check_elements",
            return_val=("test1", True),
        ):
            result = deps.gstreamer_info()
            assert "    none" in result["other"]

    @mock.patch.object(metadata, "distribution")
    def test_pkg_info(self, get_distribution_mock):
        dist_setuptools = mock.MagicMock()
        dist_setuptools.name = "setuptools"
        dist_setuptools.version = "0.6"
        dist_setuptools.locate_file = mock.MagicMock(
            return_value=Path("/tmp/example/setuptools/main.py")
        )
        dist_setuptools.requires = []

        dist_pykka = mock.Mock()
        dist_pykka.name = "Pykka"
        dist_pykka.version = "1.1"
        dist_pykka.locate_file = mock.MagicMock(
            return_value=Path("/tmp/example/pykka/main.py")
        )
        dist_pykka.requires = [f"{dist_setuptools.name}==0.6"]

        dist_mopidy = mock.Mock()
        dist_mopidy.name = "Mopidy"
        dist_mopidy.version = "0.13"
        dist_mopidy.locate_file = mock.MagicMock(
            return_value=Path("/tmp/example/mopidy/no_name.py")
        )
        dist_mopidy.requires = [f"{dist_pykka.name}==1.1"]

        get_distribution_mock.side_effect = [
            dist_mopidy,
            dist_pykka,
            dist_setuptools,
        ]

        result = deps.pkg_info()

        assert result["name"] == "Mopidy"
        assert result["version"] == "0.13"
        assert "mopidy" in str(result["path"])

        dep_info_pykka = result["dependencies"][0]
        assert dep_info_pykka["name"] == "Pykka"
        assert dep_info_pykka["version"] == "1.1"

        dep_info_setuptools = dep_info_pykka["dependencies"][0]
        assert dep_info_setuptools["name"] == "setuptools"
        assert dep_info_setuptools["version"] == "0.6"

    @mock.patch.object(metadata, "distribution")
    def test_pkg_info_for_missing_dist(self, get_distribution_mock):
        get_distribution_mock.side_effect = metadata.PackageNotFoundError("test")

        result = deps.pkg_info()

        assert result["name"] == "Mopidy"
        assert "version" not in result
        assert "path" not in result

    @pytest.mark.parametrize("include_transitive_deps", [True, False])
    @pytest.mark.parametrize("include_extras", [True, False])
    def test_pkg_info_real(self, include_transitive_deps, include_extras):
        result = deps.pkg_info(
            "Mopidy",
            include_transitive_deps=include_transitive_deps,
            include_extras=include_extras,
        )
        assert result
