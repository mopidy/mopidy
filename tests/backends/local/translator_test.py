# encoding: utf-8

from __future__ import unicode_literals

import os
import tempfile
import unittest

from mopidy.backends.local.translator import parse_m3u
from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir

data_dir = path_to_data_dir('')
song1_path = path_to_data_dir('song1.mp3')
song2_path = path_to_data_dir('song2.mp3')
encoded_path = path_to_data_dir('æøå.mp3')
song1_uri = path_to_uri(song1_path)
song2_uri = path_to_uri(song2_path)
encoded_uri = path_to_uri(encoded_path)

# FIXME use mock instead of tempfile.NamedTemporaryFile


class M3UToUriTest(unittest.TestCase):
    def test_empty_file(self):
        uris = parse_m3u(path_to_data_dir('empty.m3u'), data_dir)
        self.assertEqual([], uris)

    def test_basic_file(self):
        uris = parse_m3u(path_to_data_dir('one.m3u'), data_dir)
        self.assertEqual([song1_uri], uris)

    def test_file_with_comment(self):
        uris = parse_m3u(path_to_data_dir('comment.m3u'), data_dir)
        self.assertEqual([song1_uri], uris)

    def test_file_is_relative_to_correct_dir(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write('song1.mp3')
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path)
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_multiple_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path + '\n')
            tmp.write('# comment \n')
            tmp.write(song2_path)
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri, song2_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_uri(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_uri)
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_encoding_is_latin1(self):
        uris = parse_m3u(path_to_data_dir('encoding.m3u'), data_dir)
        self.assertEqual([encoded_uri], uris)

    def test_open_missing_file(self):
        uris = parse_m3u(path_to_data_dir('non-existant.m3u'), data_dir)
        self.assertEqual([], uris)


class URItoM3UTest(unittest.TestCase):
    pass
