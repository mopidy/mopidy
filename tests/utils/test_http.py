from __future__ import unicode_literals

import re

import pytest

from mopidy.utils import http


@pytest.mark.parametrize("config,expected", [
    ({}, None),
    ({'hostname': 'proxy.lan'}, 'http://proxy.lan:80'),
    ({'scheme': None, 'hostname': 'proxy.lan'}, 'http://proxy.lan:80'),
    ({'scheme': 'https', 'hostname': 'proxy.lan'}, 'https://proxy.lan:80'),
    ({'username': 'user', 'hostname': 'proxy.lan'}, 'http://proxy.lan:80'),
    ({'password': 'pass', 'hostname': 'proxy.lan'}, 'http://proxy.lan:80'),
    ({'hostname': 'proxy.lan', 'port': 8080}, 'http://proxy.lan:8080'),
    ({'hostname': 'proxy.lan', 'port': -1}, 'http://proxy.lan:80'),
    ({'username': 'user', 'password': 'pass', 'hostname': 'proxy.lan'},
     'http://user:pass@proxy.lan:80'),
])
def test_format_proxy(config, expected):
    assert http.format_proxy(config) == expected


@pytest.mark.parametrize("name,expected", [
    (None, r'^Mopidy/[^ ]+ CPython|/[^ ]+$'),
    ('Foo', r'^Foo Mopidy/[^ ]+ CPython|/[^ ]+$'),
    ('Foo/1.2.3', r'^Foo/1.2.3 Mopidy/[^ ]+ CPython|/[^ ]+$'),
])
def test_format_user_agent(name, expected):
    assert re.match(expected, http.format_user_agent(name))
