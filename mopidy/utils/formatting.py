from __future__ import absolute_import, unicode_literals

import re
import unicodedata


def indent(string, places=4, linebreak='\n', singles=False):
    lines = string.split(linebreak)
    if not singles and len(lines) == 1:
        return string
    for i, line in enumerate(lines):
        lines[i] = ' ' * places + line
    result = linebreak.join(lines)
    if not singles:
        result = linebreak + result
    return result


def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.

    This function is based on Django's slugify implementation.
    """
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)
