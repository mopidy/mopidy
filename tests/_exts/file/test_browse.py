import pytest

from mopidy._lib import paths
from tests import path_to_data_dir


@pytest.mark.parametrize("follow_symlinks", [True, False])
@pytest.mark.parametrize(
    ("uri", "expected_error"),
    [
        (
            "file:root",
            None,
        ),
        (
            "not_in_data_path",
            "Rejected attempt to browse path",
        ),
        (
            paths.path_to_uri(path_to_data_dir("song1.wav")),
            "Rejected attempt to browse file",
        ),
        (
            paths.path_to_uri(path_to_data_dir("")),
            None,
        ),
    ],
)
def test_file_browse(provider, uri, expected_error, caplog):
    result = provider.browse(uri)

    assert isinstance(result, list)
    if expected_error:
        assert len(result) == 0
        assert expected_error in caplog.text
    else:
        assert len(result) >= 1


@pytest.mark.parametrize(
    ("media_dirs", "expected"),
    [
        ([str(path_to_data_dir(""))], False),
        ([str(path_to_data_dir("")), str(path_to_data_dir(""))], True),
        ([], None),
        ([str(path_to_data_dir("song1.wav"))], None),
        (["|" + str(path_to_data_dir(""))], False),
    ],
)
def test_file_root_directory(provider, expected):
    ref = provider.root_directory
    if expected is None:
        assert not ref
        return
    assert ref.name == "Files"
    assert (ref.uri == "file:root") == expected
