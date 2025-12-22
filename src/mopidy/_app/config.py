from __future__ import annotations

import argparse
from typing import Any, cast

from mopidy import config as config_lib
from mopidy.commands import Command


class ConfigCommand(Command):
    help = "Show currently active configuration."

    def __init__(self) -> None:
        super().__init__()
        self.set(base_verbosity_level=-1)

    def run(
        self,
        args: argparse.Namespace,  # noqa: ARG002
        config: config_lib.Config,
        *_args: Any,
        **kwargs: Any,
    ) -> int:
        errors = cast(config_lib.ConfigErrors, kwargs.pop("errors"))
        schemas = cast(config_lib.ConfigSchemas, kwargs.pop("schemas"))

        data = config_lib.format(config, schemas, errors)

        # Throw away all bytes that are not valid UTF-8 before printing
        data = data.encode(errors="surrogateescape").decode(errors="replace")

        print(data)  # noqa: T201
        return 0
