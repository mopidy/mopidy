#encoding: utf-8

from __future__ import unicode_literals

import unittest

from mopidy.mpd import tokenize


class TestTokenizer(unittest.TestCase):
    def assertTokenizeEquals(self, expected, line):
        self.assertEqual(expected, tokenize.split(line))

    def assertTokenizeRaisesError(self, line, message=None):
        with self.assertRaises(tokenize.Error) as cm:
            tokenize.split(line)
        if message:
            self.assertEqual(cm.exception.message, message)

    def test_empty_string(self):
        self.assertTokenizeRaisesError('', 'No command given')

    def test_whitespace(self):
        self.assertTokenizeRaisesError('      ', 'No command given')
        self.assertTokenizeRaisesError('\t\t\t', 'No command given')

    def test_command(self):
        self.assertTokenizeEquals(['test'], 'test')
        self.assertTokenizeEquals(['test123'], 'test123')
        self.assertTokenizeEquals(['foo_bar'], 'foo_bar')

    def test_command_trailing_whitespace(self):
        self.assertTokenizeEquals(['test'], 'test   ')
        self.assertTokenizeEquals(['test'], 'test\t\t\t')

    def test_command_leading_whitespace(self):
        self.assertTokenizeRaisesError('  test', 'Letter expected')
        self.assertTokenizeRaisesError('\ttest', 'Letter expected')

    def test_invalid_command(self):
        self.assertTokenizeRaisesError('foo/bar', 'Invalid word character')
        self.assertTokenizeRaisesError('æøå', 'Invalid word character')
        self.assertTokenizeRaisesError('test?', 'Invalid word character')
        self.assertTokenizeRaisesError('te"st', 'Invalid word character')

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
        msg = 'Invalid unquoted character'
        self.assertTokenizeRaisesError('test par"m', msg)
        self.assertTokenizeRaisesError('test foo\bbar', msg)
        self.assertTokenizeRaisesError('test "foo"bar', msg)
        self.assertTokenizeRaisesError('test foo"bar"baz', msg)
        self.assertTokenizeRaisesError('test foo\'bar', msg)

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
        # TODO: Figure out how to check for " without space behind it.
        #msg = """Space expected after closing '"'"""
        msg = 'Invalid unquoted character'
        self.assertTokenizeRaisesError('test "par"m"', msg)

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
        msg = 'Invalid unquoted character'
        self.assertTokenizeRaisesError('test "foo bar" baz"', msg)
