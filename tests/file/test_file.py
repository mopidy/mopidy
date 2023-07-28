"""Test file (except browse and lookup)"""
from mopidy import ext
from mopidy.file import Extension
from mopidy.file.backend import FileBackend


def test_file_init():
    """Test class Extension in __init__."""
    for extension_data in ext.load_extensions():
        extension = extension_data.extension
        if isinstance(extension, Extension):
            assert extension.dist_name == "Mopidy-File"
            registry = ext.Registry()
            extension.setup(registry)
            assert registry["backend"][0] == FileBackend
            return
    raise AssertionError("Mopidy-File not loaded!")
