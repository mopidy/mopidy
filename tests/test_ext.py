from __future__ import absolute_import, unicode_literals

import mock

import pkg_resources

import pytest

from mopidy import config, exceptions, ext


class TestExtension(ext.Extension):
    dist_name = 'Mopidy-Foobar'
    ext_name = 'foobar'
    version = '1.2.3'


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


# ext.validate_extension

def test_validate_extension_name_mismatch():
    ep = mock.Mock()
    ep.name = 'barfoo'

    extension = TestExtension()
    extension.entry_point = ep

    assert not ext.validate_extension(extension)


def test_validate_extension_distribution_not_found():
    ep = mock.Mock()
    ep.name = 'foobar'
    ep.require.side_effect = pkg_resources.DistributionNotFound

    extension = TestExtension()
    extension.entry_point = ep

    assert not ext.validate_extension(extension)


def test_validate_extension_version_conflict():
    ep = mock.Mock()
    ep.name = 'foobar'
    ep.require.side_effect = pkg_resources.VersionConflict

    extension = TestExtension()
    extension.entry_point = ep

    assert not ext.validate_extension(extension)


def test_validate_extension_exception():
    ep = mock.Mock()
    ep.name = 'foobar'
    ep.require.side_effect = Exception

    extension = TestExtension()
    extension.entry_point = ep

    # We trust that entry points are well behaved, so exception will bubble.
    with pytest.raises(Exception):
        assert not ext.validate_extension(extension)


def test_validate_extension_instance_validate_env_ext_error():
    ep = mock.Mock()
    ep.name = 'foobar'

    extension = TestExtension()
    extension.entry_point = ep

    with mock.patch.object(extension, 'validate_environment') as validate:
        validate.side_effect = exceptions.ExtensionError('error')

        assert not ext.validate_extension(extension)
        validate.assert_called_once_with()


def test_validate_extension_instance_validate_env_exception():
    ep = mock.Mock()
    ep.name = 'foobar'

    extension = TestExtension()
    extension.entry_point = ep

    with mock.patch.object(extension, 'validate_environment') as validate:
        validate.side_effect = Exception

        assert not ext.validate_extension(extension)
        validate.assert_called_once_with()
