# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import tempfile
import unittest

from mopidy.m3u import translator
from mopidy.models import Track
from mopidy.utils import path

from tests import path_to_data_dir

data_dir = path_to_data_dir('')
song1_path = path_to_data_dir('song1.mp3')
song2_path = path_to_data_dir('song2.mp3')
encoded_path = path_to_data_dir('æøå.mp3')
song1_uri = path.path_to_uri(song1_path)
song2_uri = path.path_to_uri(song2_path)
encoded_uri = path.path_to_uri(encoded_path)
song1_track = Track(uri=song1_uri)
song2_track = Track(uri=song2_uri)
encoded_track = Track(uri=encoded_uri)
song1_ext_track = song1_track.replace(name='song1')
song2_ext_track = song2_track.replace(name='song2', length=60000)
encoded_ext_track = encoded_track.replace(name='æøå')


# FIXME use mock instead of tempfile.NamedTemporaryFile

class M3UToUriTest(unittest.TestCase):

    def parse(self, name):
        return translator.parse_m3u(name, data_dir)

    def test_empty_file(self):
        tracks = self.parse(path_to_data_dir('empty.m3u'))
        self.assertEqual([], tracks)

    def test_basic_file(self):
        tracks = self.parse(path_to_data_dir('one.m3u'))
        self.assertEqual([song1_track], tracks)

    def test_file_with_comment(self):
        tracks = self.parse(path_to_data_dir('comment.m3u'))
        self.assertEqual([song1_track], tracks)

    def test_file_is_relative_to_correct_dir(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write('song1.mp3')
        try:
            tracks = self.parse(tmp.name)
            self.assertEqual([song1_track], tracks)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path)
        try:
            tracks = self.parse(tmp.name)
            self.assertEqual([song1_track], tracks)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_multiple_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path + '\n')
            tmp.write('# comment \n')
            tmp.write(song2_path)
        try:
            tracks = self.parse(tmp.name)
            self.assertEqual([song1_track, song2_track], tracks)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_uri(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_uri)
        try:
            tracks = self.parse(tmp.name)
            self.assertEqual([song1_track], tracks)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_encoding_is_latin1(self):
        tracks = self.parse(path_to_data_dir('encoding.m3u'))
        self.assertEqual([encoded_track], tracks)

    def test_open_missing_file(self):
        tracks = self.parse(path_to_data_dir('non-existant.m3u'))
        self.assertEqual([], tracks)

    def test_empty_ext_file(self):
        tracks = self.parse(path_to_data_dir('empty-ext.m3u'))
        self.assertEqual([], tracks)

    def test_basic_ext_file(self):
        tracks = self.parse(path_to_data_dir('one-ext.m3u'))
        self.assertEqual([song1_ext_track], tracks)

    def test_multi_ext_file(self):
        tracks = self.parse(path_to_data_dir('two-ext.m3u'))
        self.assertEqual([song1_ext_track, song2_ext_track], tracks)

    def test_ext_file_with_comment(self):
        tracks = self.parse(path_to_data_dir('comment-ext.m3u'))
        self.assertEqual([song1_ext_track], tracks)

    def test_ext_encoding_is_latin1(self):
        tracks = self.parse(path_to_data_dir('encoding-ext.m3u'))
        self.assertEqual([encoded_ext_track], tracks)


class URItoM3UTest(unittest.TestCase):
    pass
