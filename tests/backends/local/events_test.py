from mopidy.backends.local import LocalBackend

from tests import unittest
from tests.backends.base import events


class LocalBackendEventsTest(events.BackendEventsTest, unittest.TestCase):
    backend_class = LocalBackend
