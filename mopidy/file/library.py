import base64
import imghdr
import logging
import os

from mopidy import backend, exceptions, models
from mopidy.audio import scan, tags
from mopidy.internal import path
from mopidy.models import Image

logger = logging.getLogger(__name__)


class FileLibraryProvider(backend.LibraryProvider):
    """Library for browsing local files."""

    # TODO: get_images that can pull from metadata and/or .folder.png etc?
    # TODO: handle playlists?

    @property
    def root_directory(self):
        if not self._media_dirs:
            return None
        elif len(self._media_dirs) == 1:
            uri = path.path_to_uri(self._media_dirs[0]["path"])
        else:
            uri = "file:root"
        return models.Ref.directory(name="Files", uri=uri)

    def __init__(self, backend, config):
        super().__init__(backend)
        self._media_dirs = list(self._get_media_dirs(config))
        self._cache_dir = config["core"]["cache_dir"]
        self._show_dotfiles = config["file"]["show_dotfiles"]
        self._excluded_file_extensions = tuple(
            file_ext.lower()
            for file_ext in config["file"]["excluded_file_extensions"]
        )
        self._follow_symlinks = config["file"]["follow_symlinks"]

        self._scanner = scan.Scanner(timeout=config["file"]["metadata_timeout"])

    def browse(self, uri):
        logger.debug("Browsing files at: %s", uri)
        result = []
        local_path = path.uri_to_path(uri)

        if str(local_path) == "root":
            return list(self._get_media_dirs_refs())

        if not self._is_in_basedir(local_path):
            logger.warning(
                "Rejected attempt to browse path (%s) outside dirs defined "
                "in file/media_dirs config.",
                uri,
            )
            return []

        for dir_entry in local_path.iterdir():
            child_path = dir_entry.resolve()
            uri = path.path_to_uri(child_path)

            if not self._show_dotfiles and dir_entry.name.startswith("."):
                continue

            if (
                self._excluded_file_extensions
                and dir_entry.suffix in self._excluded_file_extensions
            ):
                continue

            if child_path.is_symlink() and not self._follow_symlinks:
                logger.debug("Ignoring symlink: %s", uri)
                continue

            if not self._is_in_basedir(child_path):
                logger.debug("Ignoring symlink to outside base dir: %s", uri)
                continue

            if child_path.is_dir():
                result.append(
                    models.Ref.directory(name=dir_entry.name, uri=uri)
                )
            elif child_path.is_file():
                result.append(models.Ref.track(name=dir_entry.name, uri=uri))

        def order(item):
            return (item.type != models.Ref.DIRECTORY, item.name)

        result.sort(key=order)

        return result

    def lookup(self, uri):
        logger.debug("Looking up file URI: %s", uri)
        local_path = path.uri_to_path(uri)

        try:
            result = self._scanner.scan(uri)
            track = tags.convert_tags_to_track(result.tags).replace(
                uri=uri, length=result.duration
            )
        except exceptions.ScannerError as e:
            logger.warning("Failed looking up %s: %s", uri, e)
            track = models.Track(uri=uri)

        if not track.name:
            track = track.replace(name=local_path.name)

        return [track]

    def _get_media_dirs(self, config):
        for entry in config["file"]["media_dirs"]:
            media_dir = {}
            media_dir_split = entry.split("|", 1)
            local_path = path.expand_path(media_dir_split[0])

            if local_path is None:
                logger.debug(
                    "Failed expanding path (%s) from file/media_dirs config "
                    "value.",
                    media_dir_split[0],
                )
                continue
            elif not local_path.is_dir():
                logger.warning(
                    "%s is not a directory. Please create the directory or "
                    "update the file/media_dirs config value.",
                    local_path,
                )
                continue

            media_dir["path"] = local_path
            if len(media_dir_split) == 2:
                media_dir["name"] = media_dir_split[1]
            else:
                # TODO Mpd client should accept / in dir name
                media_dir["name"] = media_dir_split[0].replace(os.sep, "+")

            yield media_dir

    def _get_media_dirs_refs(self):
        for media_dir in self._media_dirs:
            yield models.Ref.directory(
                name=media_dir["name"], uri=path.path_to_uri(media_dir["path"])
            )

    def _is_in_basedir(self, local_path):
        return any(
            path.is_path_inside_base_dir(local_path, media_dir["path"])
            for media_dir in self._media_dirs
        )

    def get_images(self, uris):
        images = {}
        for uri in uris:
            result = self._scanner.scan(uri)
            if "image" in result.tags and len(result.tags["image"]) > 0:
                image = result.tags["image"][0]
                extension = imghdr.what("", h=image)
                images[uri] = (
                    Image(
                        uri=f"data:image/{extension};base64, "
                        f'{base64.b64encode(image).decode("utf-8")}'
                    ),
                )
            elif os.path.exists(
                os.path.join(
                    os.path.dirname(path.uri_to_path(uri)), "folder.png"
                )
            ):
                with open(
                    os.path.join(
                        os.path.dirname(path.uri_to_path(uri)), "folder.png"
                    ),
                    "rb",
                ) as f:
                    images[uri] = (
                        Image(
                            uri=f"data:image/png;base64, "
                            f'{base64.b64encode(f.read()).decode("utf-8")}'
                        ),
                    )
            elif os.path.exists(
                os.path.join(
                    os.path.dirname(path.uri_to_path(uri)), "folder.jpg"
                )
            ):
                with open(
                    os.path.join(
                        os.path.dirname(path.uri_to_path(uri)), "folder.jpg"
                    ),
                    "rb",
                ) as f:
                    images[uri] = (
                        Image(
                            uri=f"data:image/jpg;base64, "
                            f'{base64.b64encode(f.read()).decode("utf-8")}'
                        ),
                    )
            elif os.path.exists(
                os.path.join(
                    os.path.dirname(path.uri_to_path(uri)), "folder.jpeg"
                )
            ):
                with open(
                    os.path.join(
                        os.path.dirname(path.uri_to_path(uri)), "folder.jpeg"
                    ),
                    "rb",
                ) as f:
                    images[uri] = (
                        Image(
                            uri=f"data:image/jpeg;base64, "
                            f'{base64.b64encode(f.read()).decode("utf-8")}'
                        ),
                    )

            else:
                images[uri] = ()
        return images
