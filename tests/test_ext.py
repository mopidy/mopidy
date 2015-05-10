from __future__ import absolute_import, unicode_literals

import mock

import pytest

from mopidy import config, ext


# ext.Extension

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


# ext.load_extensions

class TestExtension(ext.Extension):
    dist_name = 'Mopidy-Foobar'
    ext_name = 'foobar'
    version = '1.2.3'


@mock.patch('pkg_resources.iter_entry_points')
def test_load_extensions_no_extenions(mock_entry_points):
    mock_entry_points.return_value = []
    assert [] == ext.load_extensions()


@mock.patch('pkg_resources.iter_entry_points')
def test_load_extensions(mock_entry_points):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension

    mock_entry_points.return_value = [mock_entry_point]

    extensions = ext.load_extensions()
    assert len(extensions) == 1
    assert isinstance(extensions[0], TestExtension)


@mock.patch('pkg_resources.iter_entry_points')
def test_load_extensions_gets_wrong_class(mock_entry_points):

    class WrongClass(object):
        pass

    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = WrongClass

    mock_entry_points.return_value = [mock_entry_point]

    assert [] == ext.load_extensions()


@mock.patch('pkg_resources.iter_entry_points')
def test_load_extensions_gets_instance(mock_entry_points):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension()

    mock_entry_points.return_value = [mock_entry_point]

    assert [] == ext.load_extensions()


@mock.patch('pkg_resources.iter_entry_points')
def test_load_extensions_creating_instance_fails(mock_entry_points):
    mock_extension = mock.Mock(spec=ext.Extension)
    mock_extension.side_effect = Exception

    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = mock_extension

    mock_entry_points.return_value = [mock_entry_point]
    assert [] == ext.load_extensions()


@mock.patch('pkg_resources.iter_entry_points')
def test_load_extensions_store_entry_point(mock_entry_points):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension
    mock_entry_points.return_value = [mock_entry_point]

    extensions = ext.load_extensions()
    assert len(extensions) == 1
    assert extensions[0].entry_point == mock_entry_point
