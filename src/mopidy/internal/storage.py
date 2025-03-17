import gzip
import logging
import pathlib
import tempfile

from mopidy.internal.models import StoredState

logger = logging.getLogger(__name__)


def load(path: pathlib.Path) -> StoredState | None:
    """
    Deserialize data from file.

    :param path: full path to import file
    """

    # TODO: raise an exception in case of error?
    if not path.is_file():
        logger.info("File does not exist: %s", path)
        return None
    try:
        with gzip.open(str(path), "rb") as fp:
            return StoredState.model_validate_json(fp.read())
    except (OSError, ValueError) as exc:
        logger.warning(f"Loading JSON failed: {exc}")
        return None


def dump(path: pathlib.Path, data: StoredState) -> None:
    """
    Serialize data to file.

    :param path: full path to export file
    :param data: data to serialize
    """

    # TODO: cleanup directory/basename.* files.
    tmp = tempfile.NamedTemporaryFile(  # noqa: SIM115
        prefix=path.name + ".",
        dir=str(path.parent),
        delete=False,
    )
    tmp_path = pathlib.Path(tmp.name)

    try:
        data_string = data.model_dump_json(indent=2, by_alias=True)
        with gzip.GzipFile(fileobj=tmp, mode="wb") as fp:
            fp.write(data_string.encode())
        tmp_path.rename(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
