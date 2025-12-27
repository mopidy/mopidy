from __future__ import annotations

import argparse
import configparser
import logging
import os
import pathlib
import re
from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any, cast, override

import mopidy
from mopidy._lib import paths
from mopidy.commands import Command
from mopidy.config import Config, DeprecatedValue, read

from . import config_keyring, config_schemas

if TYPE_CHECKING:
    from mopidy.config.schemas import ConfigSchema

    from .extensions import ExtensionData

logger = logging.getLogger(__name__)

type ConfigErrors = dict[str, dict[str, Any]]
type RawConfig = dict[str, dict[str, Any]]


class ConfigCommand(Command):
    help = "Show currently active configuration."

    def __init__(self) -> None:
        super().__init__()
        self.set(base_verbosity_level=-1)

    @override
    def run(
        self,
        args: argparse.Namespace,
        config: Config,
        *_args: Any,
        **kwargs: Any,
    ) -> int:
        errors = cast(ConfigErrors, kwargs.pop("errors"))
        schemas = cast(config_schemas.ConfigSchemas, kwargs.pop("schemas"))

        data = format(config, schemas, errors)

        # Throw away all bytes that are not valid UTF-8 before printing
        data = data.encode(errors="surrogateescape").decode(errors="replace")

        print(data)  # noqa: T201
        return 0


def load(
    files: list[pathlib.Path],
    ext_schemas: list[ConfigSchema],
    ext_defaults: list[str],
    overrides: list[Any],
) -> tuple[Config, ConfigErrors]:
    config_dir = pathlib.Path(__file__).parent
    defaults = [read(config_dir / "default.conf")]
    defaults.extend(ext_defaults)
    raw_config = load_raw_config(
        files, defaults, config_keyring.fetch() + (overrides or [])
    )

    schemas = config_schemas.schemas[:]
    schemas.extend(ext_schemas)
    return validate_raw_config(raw_config, schemas)


def format(  # noqa: A001
    config: Config,
    ext_schemas: config_schemas.ConfigSchemas,
    comments: dict | None = None,
    display: bool = True,
) -> str:
    schemas = config_schemas.schemas[:]
    schemas.extend(ext_schemas)
    return _format(config, comments or {}, schemas, display, False)


_INITIAL_HELP = """
# For further information about options in this file see:
#   https://docs.mopidy.com/
#
# The initial commented out values reflect the defaults as of:
#   {versions}
#
# Available options and defaults might have changed since then,
# run `mopidy config` to see the current effective config and
# `mopidy --version` to check the current version.
"""


def format_initial(extensions_data: list[ExtensionData]) -> str:
    config_dir = pathlib.Path(__file__).parent
    defaults = [read(config_dir / "default.conf")]
    defaults.extend(d.extension.get_default_config() for d in extensions_data)
    raw_config = load_raw_config([], defaults, [])

    schemas = config_schemas.schemas[:]
    schemas.extend(d.extension.get_config_schema() for d in extensions_data)

    config, _errors = validate_raw_config(raw_config, schemas)

    versions = [f"Mopidy {mopidy.__version__}"]
    extensions_data = sorted(extensions_data, key=lambda d: d.extension.dist_name)
    versions.extend(
        f"{data.extension.dist_name} {data.extension.version}"
        for data in extensions_data
    )

    header = _INITIAL_HELP.strip().format(versions="\n#   ".join(versions))
    formatted_config = _format(
        config=config,
        comments={},
        schemas=schemas,
        display=False,
        disable=True,
    )
    return header + "\n\n" + formatted_config


def load_raw_config(
    files: list[pathlib.Path],
    defaults: list[str],
    overrides: list[tuple[str, str, Any]],
) -> RawConfig:
    parser = configparser.RawConfigParser(inline_comment_prefixes=(";",))

    # TODO: simply return path to config file for defaults so we can load it
    # all in the same way?
    logger.info("Loading config from builtin defaults")
    for default in defaults:
        if isinstance(default, bytes):
            default = default.decode()
        parser.read_string(default)

    # Load config from a series of config files
    for f in files:
        f = paths.expand_path(f)
        if f.is_dir():
            for g in f.iterdir():
                if g.is_file() and g.suffix == ".conf":
                    _load_file(parser, g.resolve())
        else:
            _load_file(parser, f.resolve())

    raw_config: RawConfig = {}
    for section in parser.sections():
        raw_config[section] = dict(parser.items(section))

    logger.info("Loading config from command line options")
    for section, key, value in overrides:
        raw_config.setdefault(section, {})[key] = value

    return raw_config


def _load_file(
    parser: configparser.RawConfigParser,
    file_path: pathlib.Path,
) -> None:
    if not file_path.exists():
        logger.debug(
            f"Loading config from {file_path.as_uri()} failed; it does not exist",
        )
        return
    if not os.access(str(file_path), os.R_OK):
        logger.warning(
            f"Loading config from {file_path.as_uri()} failed; read permission missing",
        )
        return

    try:
        logger.info(f"Loading config from {file_path.as_uri()}")
        with file_path.open("r") as fh:
            parser.read_file(fh)
    except configparser.MissingSectionHeaderError:
        logger.warning(
            f"Loading config from {file_path.as_uri()} failed; "
            f"it does not have a config section",
        )
    except configparser.ParsingError as e:
        linenos = ", ".join(str(lineno) for lineno, line in e.errors)
        logger.warning(
            f"Config file {file_path.as_uri()} has errors; "
            f"line {linenos} has been ignored",
        )
    except OSError:
        # TODO: if this is the initial load of logging config we might not
        # have a logger at this point, we might want to handle this better.
        logger.debug(f"Config file {file_path.as_uri()} not found; skipping")


def validate_raw_config(
    raw_config: RawConfig,
    schemas: config_schemas.ConfigSchemas,
) -> tuple[Config, ConfigErrors]:
    # Get validated config
    config: RawConfig = {}
    errors: ConfigErrors = {}
    sections = set(raw_config)
    for schema in schemas:
        sections.discard(schema.name)
        values = raw_config.get(schema.name, {})
        result, error = schema.deserialize(values)
        if error:
            errors[schema.name] = error
        if result:
            config[schema.name] = result

    for section in sections:
        logger.warning(
            f"Ignoring config section {section!r} "
            f"because no matching extension was found",
        )

    return cast(Config, config), errors


def _format(
    config: Config,
    comments: dict[str, Any],
    schemas: config_schemas.ConfigSchemas,
    display: bool,
    disable: bool,
) -> str:
    output = []
    for schema in schemas:
        serialized = schema.serialize(
            config.get(schema.name, {}),
            display=display,
        )
        if not serialized:
            continue
        output.append(f"[{schema.name}]")
        for key, value in serialized.items():
            if isinstance(value, DeprecatedValue):
                continue
            comment = comments.get(schema.name, {}).get(key, "")
            output.append(f"{key} =")
            if value is not None:
                output[-1] += " " + value
            if comment:
                output[-1] += "  ; " + comment.capitalize()
            if disable:
                output[-1] = re.sub(r"^", "#", output[-1], flags=re.MULTILINE)
        output.append("")
    return "\n".join(output).strip()


class ReadOnlyDict(Mapping):
    def __init__(self, data: Config | dict[str, Any]) -> None:
        self._data = data

    def __getitem__(self, key: Any) -> Any:
        item = self._data.__getitem__(key)
        if isinstance(item, dict):
            return ReadOnlyDict(item)
        return item

    def __iter__(self) -> Iterator[str]:
        return self._data.__iter__()

    def __len__(self) -> int:
        return self._data.__len__()

    def __repr__(self) -> str:
        return f"ReadOnlyDict({self._data!r})"
