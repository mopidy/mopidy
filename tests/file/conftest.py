from __future__ import unicode_literals

import pytest

from mopidy.file import library


@pytest.fixture
def file_config():
    return {
        'file': {
        }
    }


@pytest.fixture
def file_library(file_config):
    return library.FileLibraryProvider(backend=None, config=file_config)
