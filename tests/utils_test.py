#encoding: utf-8

import os
import tempfile
import unittest
import urllib

from mopidy.utils import m3u_to_uris

def data(name):
    folder = os.path.dirname(__file__)
    folder = os.path.join(folder, 'data')
    folder = os.path.abspath(folder)
    return os.path.join(folder, name)


song1_path = data('song1.mp3')
song2_path = data('song2.mp3')
encoded_path = data(u'æøå.mp3')
song1_uri = 'file://' + urllib.pathname2url(song1_path)
song2_uri = 'file://' + urllib.pathname2url(song2_path)
encoded_uri = 'file://' + urllib.pathname2url(encoded_path.encode('utf-8'))


class M3UToUriTest(unittest.TestCase):
    def test_empty_file(self):
        uris = m3u_to_uris(data('empty.m3u'))
        self.assertEqual([], uris)

    def test_basic_file(self):
        uris = m3u_to_uris(data('one.m3u'))
        self.assertEqual([song1_uri], uris)

    def test_file_with_comment(self):
        uris = m3u_to_uris(data('comment.m3u'))
        self.assertEqual([song1_uri], uris)

    def test_file_with_absolute_files(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(song1_path)
            file.flush()
            uris = m3u_to_uris(file.name)
        self.assertEqual([song1_uri], uris)

    def test_file_with_multiple_absolute_files(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(song1_path+'\n')
            file.write('# comment \n')
            file.write(song2_path)
            file.flush()
            uris = m3u_to_uris(file.name)
        self.assertEqual([song1_uri, song2_uri], uris)

    def test_file_with_uri(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(song1_uri)
            file.flush()
            uris = m3u_to_uris(file.name)
        self.assertEqual([song1_uri], uris)

    def test_encoding_is_latin1(self):
        uris = m3u_to_uris(data('encoding.m3u'))
        self.assertEqual([encoded_uri], uris)
