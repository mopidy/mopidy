import pytest

from mopidy.internal import path

from tests import path_to_data_dir


@pytest.mark.parametrize("follow_symlinks", [True, False])
@pytest.mark.parametrize(
    "uri, levelname",
    [
        ("file:root", None),
        ("not_in_data_path", "WARNING"),
        (path.path_to_uri(path_to_data_dir("song1.wav")), "ERROR"),
        (path.path_to_uri(path_to_data_dir("")), None),
    ],
)
def test_file_browse(provider, uri, levelname, caplog):
    result = provider.browse(uri)
    assert type(result) is list
    if levelname:
        assert len(result) == 0
        record = caplog.records[0]
        assert record.levelname == levelname
        assert "Rejected attempt" in record.message
        return

    assert len(result) >= 1


@pytest.mark.parametrize(
    "media_dirs, expected",
    [
        ([str(path_to_data_dir(""))], False),
        ([str(path_to_data_dir("")), str(path_to_data_dir(""))], True),
        ([], None),
        ([str(path_to_data_dir("song1.wav"))], None),
        (["|" + str(path_to_data_dir(""))], False),
        ([str(path_to_data_dir("$"))], None),
    ],
)
def test_file_root_directory(provider, expected):
    """Test root_directory()"""
    ref = provider.root_directory
    if expected is None:
        assert not ref
        return
    assert ref.name == "Files"
    assert (ref.uri == "file:root") == expected
