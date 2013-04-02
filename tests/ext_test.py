from __future__ import unicode_literals

from mopidy.ext import Extension
from mopidy.utils import config

from tests import unittest


class ExtensionTest(unittest.TestCase):
    def setUp(self):
        self.ext = Extension()

    def test_name_is_none(self):
        self.assertIsNone(self.ext.name)

    def test_version_is_none(self):
        self.assertIsNone(self.ext.version)

    def test_get_default_config_raises_not_implemented(self):
        self.assertRaises(NotImplementedError, self.ext.get_default_config)

    def test_get_config_schema_returns_extension_schema(self):
        schema = self.ext.get_config_schema()
        self.assertIsInstance(schema, config.ExtensionConfigSchema)
        self.assertIsInstance(schema['enabled'], config.Boolean)

    def test_validate_environment_does_nothing_by_default(self):
        self.assertIsNone(self.ext.validate_environment())

    def test_get_frontend_classes_returns_an_empty_list(self):
        self.assertListEqual(self.ext.get_frontend_classes(), [])

    def test_get_backend_classes_returns_an_empty_list(self):
        self.assertListEqual(self.ext.get_backend_classes(), [])

    def test_register_gstreamer_elements_does_nothing_by_default(self):
        self.assertIsNone(self.ext.register_gstreamer_elements())
