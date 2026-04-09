class MopidyException(Exception):  # noqa: N818
    """Base class for all Mopidy exceptions."""


class AudioException(MopidyException):
    """Raised when the audio layer encounters an error."""


class BackendError(MopidyException):
    """Raised when a backend encounters an error."""


class CoreError(MopidyException):
    """Raised when the core encounters an error."""


class ExtensionError(MopidyException):
    """Raised when an extension fails environment validation or setup."""


class FrontendError(MopidyException):
    """Raised when a frontend encounters an error."""


class MixerError(MopidyException):
    """Raised when a mixer encounters an error."""


class ScannerError(MopidyException):
    """Raised when the file scanner encounters an error."""


class TracklistFull(CoreError):  # noqa: N818
    """Raised when the tracklist cannot accept more tracks."""


class ValidationError(ValueError):
    """Raised when an API argument fails validation."""
