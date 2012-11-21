from __future__ import unicode_literals

import re
import unicodedata


def indent(string, places=4, linebreak='\n'):
    lines = string.split(linebreak)
    if len(lines) == 1:
        return string
    result = ''
    for line in lines:
        result += linebreak + ' ' * places + line
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
