from __future__ import absolute_import, unicode_literals

import unittest

from mopidy import exceptions


class ExceptionsTest(unittest.TestCase):

    def test_exception_can_include_message_string(self):
        exc = exceptions.MopidyException('foo')

        self.assertEqual(exc.message, 'foo')
        self.assertEqual(str(exc), 'foo')

    def test_backend_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.BackendError, exceptions.MopidyException))

    def test_extension_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.ExtensionError, exceptions.MopidyException))

    def test_find_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.FindError, exceptions.MopidyException))

    def test_find_error_can_store_an_errno(self):
        exc = exceptions.FindError('msg', errno=1234)

        self.assertEqual(exc.message, 'msg')
        self.assertEqual(exc.errno, 1234)

    def test_frontend_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.FrontendError, exceptions.MopidyException))

    def test_mixer_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.MixerError, exceptions.MopidyException))

    def test_scanner_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.ScannerError, exceptions.MopidyException))

    def test_audio_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.AudioException, exceptions.MopidyException))
