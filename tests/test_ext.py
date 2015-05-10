from __future__ import absolute_import, unicode_literals

import pytest

from mopidy import config, ext


@pytest.fixture
def extension():
    return ext.Extension()


def test_dist_name_is_none(extension):
    assert extension.dist_name is None


def test_ext_name_is_none(extension):
    assert extension.ext_name is None


def test_version_is_none(extension):
    assert extension.version is None


def test_get_default_config_raises_not_implemented(extension):
    with pytest.raises(NotImplementedError):
        extension.get_default_config()


def test_get_config_schema_returns_extension_schema(extension):
    schema = extension.get_config_schema()
    assert isinstance(schema['enabled'], config.Boolean)


def test_validate_environment_does_nothing_by_default(extension):
    assert extension.validate_environment() is None


def test_setup_raises_not_implemented(extension):
    with pytest.raises(NotImplementedError):
        extension.setup(None)
