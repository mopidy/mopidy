from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any, override

from mopidy.commands import Command
from mopidy.internal import deps

if TYPE_CHECKING:
    from mopidy.config import Config


class DepsCommand(Command):
    help = "Show dependencies and debug information."

    def __init__(self) -> None:
        super().__init__()
        self.set(base_verbosity_level=-1)

    @override
    def run(
        self,
        args: argparse.Namespace,
        config: Config,
        *_args: Any,
        **_kwargs: Any,
    ) -> int:
        print(deps.format_dependency_list())  # noqa: T201
        return 0
