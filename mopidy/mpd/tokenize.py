from __future__ import unicode_literals

import re


class TokenizeError(Exception):
    pass


WORD_RE = re.compile(r"""
    ^                 # Leading whitespace is not allowed
    ([a-z][a-z0-9_]*) # A command name
    (?:\s+|$)         # trailing whitespace or EOS
    (.*)              # Possibly a remainder to be parsed
    """, re.VERBOSE)

# Quotes matching is an unrolled version of "(?:[^"\\]|\\.)*"
PARAM_RE = re.compile(r"""
    ^                               # Leading whitespace is not allowed
    (?:
        ([^%(unprintable)s"\\]+)    # ord(char) < 0x20, not ", not backslash
        |                           # or
        "([^"\\]*(?:\\.[^"\\]*)*)"  # anything surrounded by quotes
    )
    (?:\s+|$)                       # trailing whitespace or EOS
    (.*)                            # Possibly a remainder to be parsed
    """ % {'unprintable': ''.join(map(chr, range(0x21)))}, re.VERBOSE)

UNESCAPE_RE = re.compile(r'\\(.)')  # Backslash escapes any following char.


def split(line):
    match = WORD_RE.match(line)
    if not match:
        raise TokenizeError('Invalid word')
    command, remainder = match.groups()
    result = [command]

    while remainder:
        match = PARAM_RE.match(remainder)
        if not match:
            raise TokenizeError('Invalid parameter')
        unquoted, quoted, remainder = match.groups()
        result.append(unquoted or UNESCAPE_RE.sub(r'\g<1>', quoted))

    return result
