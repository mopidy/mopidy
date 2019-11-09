import unittest
from unittest import mock

import pykka

from mopidy import core
from mopidy.internal import deprecation
from mopidy.mpd import session, uri_mapper

from tests import dummy_audio, dummy_backend, dummy_mixer


class MockConnection(mock.Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = mock.sentinel.host
        self.port = mock.sentinel.port
        self.response = []

    def queue_send(self, data):
        data = data.decode()
        lines = (line for line in data.split("\n") if line)
        self.response.extend(lines)


class BaseTestCase(unittest.TestCase):
    enable_mixer = True

    def get_config(self):
        return {
            "core": {"max_tracklist_length": 10000},
            "mpd": {"password": None, "default_playlist_scheme": "dummy"},
        }

    def setUp(self):  # noqa: N802
        if self.enable_mixer:
            self.mixer = dummy_mixer.create_proxy()
        else:
            self.mixer = None
        self.audio = dummy_audio.create_proxy()
        self.backend = dummy_backend.create_proxy(audio=self.audio)

        with deprecation.ignore():
            self.core = core.Core.start(
                self.get_config(),
                audio=self.audio,
                mixer=self.mixer,
                backends=[self.backend],
            ).proxy()

        self.uri_map = uri_mapper.MpdUriMapper(self.core)
        self.connection = MockConnection()
        self.session = session.MpdSession(
            self.connection,
            config=self.get_config(),
            core=self.core,
            uri_map=self.uri_map,
        )
        self.dispatcher = self.session.dispatcher
        self.context = self.dispatcher.context

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def send_request(self, request):
        self.connection.response = []
        request = f"{request}\n".encode()
        self.session.on_receive({"received": request})
        return self.connection.response

    def assertNoResponse(self):  # noqa: N802
        assert [] == self.connection.response

    def assertInResponse(self, value):  # noqa: N802
        assert (
            value in self.connection.response
        ), f"Did not find {value!r} in {self.connection.response!r}"

    def assertOnceInResponse(self, value):  # noqa: N802
        matched = len([r for r in self.connection.response if r == value])
        assert (
            1 == matched
        ), f"Expected to find {value!r} once in {self.connection.response!r}"

    def assertNotInResponse(self, value):  # noqa: N802
        assert (
            value not in self.connection.response
        ), f"Found {value!r} in {self.connection.response!r}"

    def assertEqualResponse(self, value):  # noqa: N802
        assert 1 == len(self.connection.response)
        assert value == self.connection.response[0]
