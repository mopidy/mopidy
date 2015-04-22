# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import pytest

from mopidy.utils import search


@pytest.mark.parametrize("value,expected", [
    ('abc', ['abc']),
    ('abc def', ['abc', 'def']),
    ('abc ', ['abc']),
    (' abc ', ['abc']),
    ('æøå', ['æøå']),
    ('AbC', ['AbC']),
    ('foo-bar', ['foo-bar']),
    ('foo_bar', ['foo_bar']),
    ('foo$bar', ['foo$bar']),
    ('\x10', ['\x10']),
    ('    ', []),
    ('\n', []),
    ('\t', []),
    ('', []),
    ('abc:', []),
    ('foo_bar:', []),
    ('Foo_bar:', []),
    ('abc : def', ['abc', 'def']),
    ('foo-bar:', []),
    ('"abc ABC"', []),
])
def test_term_regexp(value, expected):
    assert search.TERM_RE.findall(value) == expected


@pytest.mark.parametrize("value,expected", [
    ('abc:', ['abc']),
    ('foo_bar:', ['foo_bar']),
    ('abc', []),
    ('abc : def', []),
    ('æøå:', []),
    ('foo-bar:', []),
    ('Foo_bar:', []),
])
def test_field_regexp(value, expected):
    assert search.FIELD_RE.findall(value) == expected


@pytest.mark.parametrize("value,expected", [
    ('"abc ABC"', ['abc ABC']),
    ('"abc\nABC"', ['abc\nABC']),
    ('"abc \\" ABC"', ['abc \\" ABC']),
    ('"abc ABC" "', ['abc ABC']),
    ('""', ['']),
    ('"æøå"', ['æøå']),
])
def test_phrase_regexp(value, expected):
    assert search.PHRASE_RE.findall(value) == expected


@pytest.mark.parametrize("value,expected", [
    ('', []),
    ('   ', []),

    ('""', [(None, '')]),
    ('"  "', [(None, '  ')]),
    ('"" ""', [(None, ''), (None, '')]),

    ('test', [(None, 'test')]),
    ('test    ', [(None, 'test')]),
    ('    test', [(None, 'test')]),
    ('"test"', [(None, 'test')]),
    ('"abc def"', [(None, 'abc def')]),
    ('"\\""', [(None, '"')]),
    ('"\\n"', [(None, '\n')]),
    ('æøå', [(None, 'æøå')]),
    ('"æøå"', [(None, 'æøå')]),
    ('"foo:bar"', [(None, 'foo:bar')]),

    ('"foo" "bar', [(None, 'foo')]),
    ('foo" bar "baz', [(None, 'bar')]),

    ('foo:test', [('foo', 'test')]),
    ('foo:"test"', [('foo', 'test')]),
    ('foo:"abc def"', [('foo', 'abc def')]),

    ('foo:""', [('foo', '')]),
    ('foo:"  "', [('foo', '  ')]),

    ('foo:bar baz', [('foo', 'bar'), (None, 'baz')]),
    ('foo:bar "baz abc"', [('foo', 'bar'), (None, 'baz abc')]),

    ('abc def', [(None, 'abc'), (None, 'def')]),
    ('"abc def" 123', [(None, 'abc def'), (None, '123')]),
    ('foo : bar', [(None, 'foo'), (None, 'bar')]),

    ('foo:', []),
    ('Foo:', []),
    ('Bar:baz', []),
    ('foo-bar:baz', []),
    ('foo:foo:foo', []),
    ('"foo":', []),
    ('æøå:', []),

    ('"foo"bar', []),
    ('"foo bar"baz', []),
    ('foo" "bar', []),
    ('"""', []),
    ('""""', []),
])
def test_parse(value, expected):
    assert list(search.parse(value)) == expected
