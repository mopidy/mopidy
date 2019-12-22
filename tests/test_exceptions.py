import unittest

from mopidy import exceptions


class ExceptionsTest(unittest.TestCase):
    def test_exception_can_include_message_string(self):
        exc = exceptions.MopidyException("foo")

        assert exc.message == "foo"
        assert str(exc) == "foo"

    def test_backend_error_is_a_mopidy_exception(self):
        assert issubclass(exceptions.BackendError, exceptions.MopidyException)

    def test_extension_error_is_a_mopidy_exception(self):
        assert issubclass(exceptions.ExtensionError, exceptions.MopidyException)

    def test_frontend_error_is_a_mopidy_exception(self):
        assert issubclass(exceptions.FrontendError, exceptions.MopidyException)

    def test_mixer_error_is_a_mopidy_exception(self):
        assert issubclass(exceptions.MixerError, exceptions.MopidyException)

    def test_scanner_error_is_a_mopidy_exception(self):
        assert issubclass(exceptions.ScannerError, exceptions.MopidyException)

    def test_audio_error_is_a_mopidy_exception(self):
        assert issubclass(exceptions.AudioException, exceptions.MopidyException)
