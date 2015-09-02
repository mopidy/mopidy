from __future__ import absolute_import, unicode_literals

from mopidy import config


def test_core_schema_has_cache_dir():
    assert 'cache_dir' in config._core_schema
    assert isinstance(config._core_schema['cache_dir'], config.Path)


def test_core_schema_has_config_dir():
    assert 'config_dir' in config._core_schema
    assert isinstance(config._core_schema['config_dir'], config.Path)


def test_core_schema_has_data_dir():
    assert 'data_dir' in config._core_schema
    assert isinstance(config._core_schema['data_dir'], config.Path)


def test_core_schema_has_max_tracklist_length():
    assert 'max_tracklist_length' in config._core_schema
    max_tracklist_length_schema = config._core_schema['max_tracklist_length']
    assert isinstance(max_tracklist_length_schema, config.Integer)
    assert max_tracklist_length_schema._minimum == 1
    assert max_tracklist_length_schema._maximum == 10000
