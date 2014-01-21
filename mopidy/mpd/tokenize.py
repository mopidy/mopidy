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

BAD_QUOTED_PARAM_RE = re.compile(r"""
    ^
    "[^"\\]*(?:\\.[^"\\]*)*  # start of a quoted value
    (?:                      # followed by:
        ("[^\s])             # non-escaped quote, followed by non-whitespace
        |                    # or
        ([^"])               # anything that is not a quote
    )
    """, re.VERBOSE)

UNESCAPE_RE = re.compile(r'\\(.)')  # Backslash escapes any following char.


def split(line):
    if not line.strip():
        raise Error('No command given')  # 5@0
    match = WORD_RE.match(line)
    if not match:
        raise Error('Invalid word character')  # 5@0
    whitespace, command, remainder = match.groups()
    if whitespace:
        raise Error('Letter expected')  # 5@0

    result = [command]
    while remainder:
        match = PARAM_RE.match(remainder)
        if not match:
            # Following checks are simply to match MPD error messages:
            match = BAD_QUOTED_PARAM_RE.match(remainder)
            if match:
                if match.group(1):
                    raise Error('Space expected after closing \'"\'')  # 2@0
                else:
                    raise Error('Missing closing \'"\'')  # 2@0
            raise Error('Invalid unquoted character')  # 2@0
        unquoted, quoted, remainder = match.groups()
        result.append(unquoted or UNESCAPE_RE.sub(r'\g<1>', quoted))

    return result
