from __future__ import unicode_literals

import pytest


@pytest.fixture
def file_config():
    return {
        'file': {
        }
    }


@pytest.fixture
def file_library(file_config):
    # Import library, thus scanner, thus gobject as late as possible to avoid
    # hard to track import errors during conftest setup.
    from mopidy.file import library

    return library.FileLibraryProvider(backend=None, config=file_config)
