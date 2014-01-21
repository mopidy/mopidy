from __future__ import unicode_literals

import re


class Error(Exception):
    pass


WORD_RE = re.compile(r"""
    ^
    (\s*)             # Leading whitespace not allowed, capture it to report.
    ([a-z][a-z0-9_]*) # A command name
    (?:\s+|$)         # trailing whitespace or EOS
    (.*)              # Possibly a remainder to be parsed
    """, re.VERBOSE)

# Quotes matching is an unrolled version of "(?:[^"\\]|\\.)*"
PARAM_RE = re.compile(r"""
    ^                               # Leading whitespace is not allowed
    (?:
        ([^%(unprintable)s"']+)     # ord(char) < 0x20, not ", not '
        |                           # or
        "([^"\\]*(?:\\.[^"\\]*)*)"  # anything surrounded by quotes
    )
    (?:\s+|$)                       # trailing whitespace or EOS
    (.*)                            # Possibly a remainder to be parsed
    """ % {'unprintable': ''.join(map(chr, range(0x21)))}, re.VERBOSE)

UNESCAPE_RE = re.compile(r'\\(.)')  # Backslash escapes any following char.


def split(line):
    if not line.strip():
        raise Error('No command given')
    match = WORD_RE.match(line)
    if not match:
        raise Error('Invalid word character')
    whitespace, command, remainder = match.groups()
    if whitespace:
        raise Error('Letter expected')
    result = [command]

    while remainder:
        match = PARAM_RE.match(remainder)
        if not match:
            raise Error('Invalid unquoted character')
        unquoted, quoted, remainder = match.groups()
        result.append(unquoted or UNESCAPE_RE.sub(r'\g<1>', quoted))

    return result
