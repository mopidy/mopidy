from __future__ import absolute_import, unicode_literals

import re

_unprintable = r'\x00-\x20\x7f-\xa0'
_field = r'(?P<field>[a-z][a-z_]*):'
_phrase = r'"(?P<phrase>[^"\\]*(?:\\.[^"\\]*)*)"'
_term = r'(?P<term>[^":%s]+)' % _unprintable
_query = r'(?:%s)?(?:%s|%s)' % (_field, _phrase, _term)

# Ugh, the lookahead/behinds are rather ugly :/
_wrapper = r'(?:(?<=\s)|^)%s(?:(?=\s)|$)'

FIELD_RE = re.compile(_wrapper % _field)
PHRASE_RE = re.compile(_wrapper % _phrase)
QUERY_RE = re.compile(_wrapper % _query)
TERM_RE = re.compile(_wrapper % _term)


def parse(query):
    for m in QUERY_RE.finditer(query):
        result = m.groupdict()
        if result['phrase'] is not None:
            value = result['phrase'].encode('utf-8')
            value = value.decode('string_escape')
            yield result['field'], value.decode('utf-8')
        else:
            yield result['field'], result['term']
