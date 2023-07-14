import copy

from mopidy.file.library import FileLibraryProvider

from tests import path_to_data_dir


def test_file_browse(provider, track_uri, caplog):
    result = provider.browse(track_uri)

    assert len(result) == 0
    assert any(map(lambda record: record.levelname == "ERROR", caplog.records))
    assert any(
        map(lambda record: "Rejected attempt" in record.message, caplog.records)
    )


def test_file_root_directory(config):
    """Test root_directory()"""
    root_config = copy.deepcopy(config)
    mopidy_file = FileLibraryProvider(None, root_config)
    ref = mopidy_file.root_directory
    assert ref.ALBUM == "album"
    root_config["file"]["media_dirs"].append(str(path_to_data_dir("")))
    mopidy_file = FileLibraryProvider(None, root_config)
    ref = mopidy_file.root_directory
    assert ref.ALBUM == "album"
    root_config["file"]["media_dirs"] = []
    mopidy_file = FileLibraryProvider(None, root_config)
    assert not mopidy_file.root_directory
