# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.mpd import exceptions, tokenize


class TestTokenizer(unittest.TestCase):

    def assertTokenizeEquals(self, expected, line):  # noqa: N802
        self.assertEqual(expected, tokenize.split(line))

    def assertTokenizeRaises(self, exception, message, line):  # noqa: N802
        with self.assertRaises(exception) as cm:
            tokenize.split(line)
        self.assertEqual(cm.exception.message, message)

    def test_empty_string(self):
        ex = exceptions.MpdNoCommand
        msg = 'No command given'
        self.assertTokenizeRaises(ex, msg, '')
        self.assertTokenizeRaises(ex, msg, '      ')
        self.assertTokenizeRaises(ex, msg, '\t\t\t')

    def test_command(self):
        self.assertTokenizeEquals(['test'], 'test')
        self.assertTokenizeEquals(['test123'], 'test123')
        self.assertTokenizeEquals(['foo_bar'], 'foo_bar')

    def test_command_trailing_whitespace(self):
        self.assertTokenizeEquals(['test'], 'test   ')
        self.assertTokenizeEquals(['test'], 'test\t\t\t')

    def test_command_leading_whitespace(self):
        ex = exceptions.MpdUnknownError
        msg = 'Letter expected'
        self.assertTokenizeRaises(ex, msg, '  test')
        self.assertTokenizeRaises(ex, msg, '\ttest')

    def test_invalid_command(self):
        ex = exceptions.MpdUnknownError
        msg = 'Invalid word character'
        self.assertTokenizeRaises(ex, msg, 'foo/bar')
        self.assertTokenizeRaises(ex, msg, 'æøå')
        self.assertTokenizeRaises(ex, msg, 'test?')
        self.assertTokenizeRaises(ex, msg, 'te"st')

    def test_unquoted_param(self):
        self.assertTokenizeEquals(['test', 'param'], 'test param')
        self.assertTokenizeEquals(['test', 'param'], 'test\tparam')

    def test_unquoted_param_leading_whitespace(self):
        self.assertTokenizeEquals(['test', 'param'], 'test  param')
        self.assertTokenizeEquals(['test', 'param'], 'test\t\tparam')

    def test_unquoted_param_trailing_whitespace(self):
        self.assertTokenizeEquals(['test', 'param'], 'test param  ')
        self.assertTokenizeEquals(['test', 'param'], 'test param\t\t')

    def test_unquoted_param_invalid_chars(self):
        ex = exceptions.MpdArgError
        msg = 'Invalid unquoted character'
        self.assertTokenizeRaises(ex, msg, 'test par"m')
        self.assertTokenizeRaises(ex, msg, 'test foo\bbar')
        self.assertTokenizeRaises(ex, msg, 'test foo"bar"baz')
        self.assertTokenizeRaises(ex, msg, 'test foo\'bar')

    def test_unquoted_param_numbers(self):
        self.assertTokenizeEquals(['test', '123'], 'test 123')
        self.assertTokenizeEquals(['test', '+123'], 'test +123')
        self.assertTokenizeEquals(['test', '-123'], 'test -123')
        self.assertTokenizeEquals(['test', '3.14'], 'test 3.14')

    def test_unquoted_param_extended_chars(self):
        self.assertTokenizeEquals(['test', 'æøå'], 'test æøå')
        self.assertTokenizeEquals(['test', '?#$'], 'test ?#$')
        self.assertTokenizeEquals(['test', '/foo/bar/'], 'test /foo/bar/')
        self.assertTokenizeEquals(['test', 'foo\\bar'], 'test foo\\bar')

    def test_unquoted_params(self):
        self.assertTokenizeEquals(['test', 'foo', 'bar'], 'test foo bar')

    def test_quoted_param(self):
        self.assertTokenizeEquals(['test', 'param'], 'test "param"')
        self.assertTokenizeEquals(['test', 'param'], 'test\t"param"')

    def test_quoted_param_leading_whitespace(self):
        self.assertTokenizeEquals(['test', 'param'], 'test  "param"')
        self.assertTokenizeEquals(['test', 'param'], 'test\t\t"param"')

    def test_quoted_param_trailing_whitespace(self):
        self.assertTokenizeEquals(['test', 'param'], 'test "param"  ')
        self.assertTokenizeEquals(['test', 'param'], 'test "param"\t\t')

    def test_quoted_param_invalid_chars(self):
        ex = exceptions.MpdArgError
        msg = 'Space expected after closing \'"\''
        self.assertTokenizeRaises(ex, msg, 'test "foo"bar"')
        self.assertTokenizeRaises(ex, msg, 'test "foo"bar" ')
        self.assertTokenizeRaises(ex, msg, 'test "foo"bar')
        self.assertTokenizeRaises(ex, msg, 'test "foo"bar ')

    def test_quoted_param_numbers(self):
        self.assertTokenizeEquals(['test', '123'], 'test "123"')
        self.assertTokenizeEquals(['test', '+123'], 'test "+123"')
        self.assertTokenizeEquals(['test', '-123'], 'test "-123"')
        self.assertTokenizeEquals(['test', '3.14'], 'test "3.14"')

    def test_quoted_param_spaces(self):
        self.assertTokenizeEquals(['test', 'foo bar'], 'test "foo bar"')
        self.assertTokenizeEquals(['test', 'foo bar'], 'test "foo bar"')
        self.assertTokenizeEquals(['test', ' param\t'], 'test " param\t"')

    def test_quoted_param_extended_chars(self):
        self.assertTokenizeEquals(['test', 'æøå'], 'test "æøå"')
        self.assertTokenizeEquals(['test', '?#$'], 'test "?#$"')
        self.assertTokenizeEquals(['test', '/foo/bar/'], 'test "/foo/bar/"')

    def test_quoted_param_escaping(self):
        self.assertTokenizeEquals(['test', '\\'], r'test "\\"')
        self.assertTokenizeEquals(['test', '"'], r'test "\""')
        self.assertTokenizeEquals(['test', ' '], r'test "\ "')
        self.assertTokenizeEquals(['test', '\\n'], r'test "\\\n"')

    def test_quoted_params(self):
        self.assertTokenizeEquals(['test', 'foo', 'bar'], 'test "foo" "bar"')

    def test_mixed_params(self):
        self.assertTokenizeEquals(['test', 'foo', 'bar'], 'test foo "bar"')
        self.assertTokenizeEquals(['test', 'foo', 'bar'], 'test "foo" bar')
        self.assertTokenizeEquals(['test', '1', '2'], 'test 1 "2"')
        self.assertTokenizeEquals(['test', '1', '2'], 'test "1" 2')

        self.assertTokenizeEquals(['test', 'foo bar', 'baz', '123'],
                                  'test "foo bar" baz 123')
        self.assertTokenizeEquals(['test', 'foo"bar', 'baz', '123'],
                                  r'test "foo\"bar" baz 123')

    def test_unbalanced_quotes(self):
        ex = exceptions.MpdArgError
        msg = 'Invalid unquoted character'
        self.assertTokenizeRaises(ex, msg, 'test "foo bar" baz"')

    def test_missing_closing_quote(self):
        ex = exceptions.MpdArgError
        msg = 'Missing closing \'"\''
        self.assertTokenizeRaises(ex, msg, 'test "foo')
        self.assertTokenizeRaises(ex, msg, 'test "foo a ')
