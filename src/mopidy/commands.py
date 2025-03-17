from __future__ import annotations

import argparse
import collections
import contextlib
import logging
import signal
import sys
from collections.abc import Generator, Iterable, Sequence
from pathlib import Path
from typing import (
    Any,
    NoReturn,
    cast,
)

import pykka
from pykka import ThreadingActor
from pykka.messages import ProxyCall

import mopidy
from mopidy import config as config_lib
from mopidy import exceptions
from mopidy.audio import Audio, AudioProxy
from mopidy.backend import BackendActor, BackendProxy
from mopidy.core import Core, CoreProxy
from mopidy.internal import deps, process, timer
from mopidy.internal.gi import GLib
from mopidy.mixer import MixerActor, MixerProxy
from mopidy.types import Percentage

logger = logging.getLogger(__name__)


def config_files_type(value: str) -> list[str]:
    return value.split(":")


def config_override_type(value: str) -> tuple[str, str, str]:
    try:
        section, remainder = value.split("/", 1)
        key, value = remainder.split("=", 1)
        return (section.strip(), key.strip(), value.strip())
    except ValueError as exc:
        msg = f"{value} must have the format section/key=value"
        raise argparse.ArgumentTypeError(msg) from exc


class _ParserError(Exception):
    def __init__(self, message) -> None:
        self.message = message


class _HelpError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message) -> NoReturn:
        raise _ParserError(message)


class _HelpAction(argparse.Action):
    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str | None = None,
        help: str | None = None,
    ) -> None:
        super().__init__(
            option_strings=option_strings,
            dest=dest or argparse.SUPPRESS,
            default=argparse.SUPPRESS,
            nargs=0,
            help=help,
        )

    def __call__(
        self,
        parser,  # noqa: ARG002
        namespace,  # noqa: ARG002
        values,  # noqa: ARG002
        option_string=None,  # noqa: ARG002
    ) -> NoReturn:
        raise _HelpError


class Command:
    """Command parser and runner for building trees of commands.

    This class provides a wrapper around :class:`argparse.ArgumentParser`
    for handling this type of command line application in a better way than
    argparse's own sub-parser handling.
    """

    help: str | None = None
    #: Help text to display in help output.

    _children: dict[str, Command]
    _arguments: list[tuple[tuple[Any, ...], dict[str, Any]]]
    _overrides: dict[str, Any]

    def __init__(self) -> None:
        self._children = collections.OrderedDict()
        self._arguments = []
        self._overrides = {}

    def _build(self) -> tuple[_ArgumentParser, list[argparse.Action]]:
        actions: list[argparse.Action] = []
        parser = _ArgumentParser(add_help=False)
        parser.register("action", "help", _HelpAction)

        for args, kwargs in self._arguments:
            actions.append(parser.add_argument(*args, **kwargs))

        parser.add_argument("_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
        return parser, actions

    def add_child(self, name: str, command: Command) -> None:
        """Add a child parser to consider using.

        :param name: name to use for the sub-command that is being added.
        :param command: the command to add.
        """
        self._children[name] = command

    def add_argument(self, *args: Any, **kwargs: Any) -> None:
        """Add an argument to the parser.

        This method takes all the same arguments as the
        :class:`argparse.ArgumentParser` version of this method.
        """
        self._arguments.append((args, kwargs))

    def set(self, **kwargs: Any) -> None:
        """Override a value in the finaly result of parsing."""
        self._overrides.update(kwargs)

    def exit(
        self,
        status_code: int = 0,
        message: str | None = None,
        usage: str | None = None,
    ) -> NoReturn:
        """Optionally print a message and exit."""
        print("\n\n".join(m for m in (usage, message) if m))  # noqa: T201
        sys.exit(status_code)

    def format_usage(self, prog: str | None = None) -> str:
        """Format usage for current parser."""
        actions = self._build()[1]
        prog = prog or Path(sys.argv[0]).name
        return self._usage(actions, prog) + "\n"

    def _usage(self, actions: Iterable[argparse.Action], prog) -> str:
        formatter = argparse.HelpFormatter(prog)
        formatter.add_usage(None, actions, [])
        return formatter.format_help().strip()

    def format_help(self, prog: str | None = None) -> str:
        """Format help for current parser and children."""
        actions = self._build()[1]
        prog = prog or Path(sys.argv[0]).name

        formatter = argparse.HelpFormatter(prog)
        formatter.add_usage(None, actions, [])

        if self.help:
            formatter.add_text(self.help)

        if actions:
            formatter.add_text("OPTIONS:")
            formatter.start_section(None)
            formatter.add_arguments(actions)
            formatter.end_section()

        subhelp = []
        for name, child in self._children.items():
            child._subhelp(name, subhelp)

        if subhelp:
            formatter.add_text("COMMANDS:")
            subhelp.insert(0, "")

        return formatter.format_help() + "\n".join(subhelp)

    def _subhelp(self, name: str, result: list[str]) -> None:
        actions = self._build()[1]

        if self.help or actions:
            formatter = argparse.HelpFormatter(name)
            formatter.add_usage(None, actions, [], "")
            formatter.start_section(None)
            formatter.add_text(self.help)
            formatter.start_section(None)
            formatter.add_arguments(actions)
            formatter.end_section()
            formatter.end_section()
            result.append(formatter.format_help())

        for childname, child in self._children.items():
            child._subhelp(f"{name} {childname}", result)

    def parse(self, args: list[str], prog: str | None = None) -> argparse.Namespace:
        """Parse command line arguments.

        Will recursively parse commands until a final parser is found or an
        error occurs. In the case of errors we will print a message and exit.
        Otherwise, any overrides are applied and the current parser stored
        in the command attribute of the return value.

        :param args: list of arguments to parse
        :param prog: name to use for program
        """
        prog = prog or Path(sys.argv[0]).name
        try:
            return self._parse(
                args,
                argparse.Namespace(),
                self._overrides.copy(),
                prog,
            )
        except _HelpError:
            self.exit(0, self.format_help(prog))

    def _parse(
        self,
        args: Sequence[str],
        namespace: argparse.Namespace,
        overrides: dict[str, Any],
        prog: str,
    ) -> argparse.Namespace:
        overrides.update(self._overrides)
        parser, actions = self._build()

        try:
            result = parser.parse_args(args, namespace)
        except _ParserError as exc:
            self.exit(1, str(exc), self._usage(actions, prog))

        if not result._args:
            for attr, value in overrides.items():
                setattr(result, attr, value)
            delattr(result, "_args")
            result.command = self
            return result

        child = result._args.pop(0)
        if child not in self._children:
            usage = self._usage(actions, prog)
            self.exit(1, f"unrecognized command: {child}", usage)

        return self._children[child]._parse(
            result._args,
            result,
            overrides,
            f"{prog} {child}",
        )

    def run(
        self,
        args: argparse.Namespace,
        config: config_lib.Config,
        *_args: Any,
        **_kwargs: Any,
    ) -> int:
        """Run the command.

        Must be implemented by sub-classes that are not simply an intermediate
        in the command namespace.
        """
        raise NotImplementedError


@contextlib.contextmanager
def _actor_error_handling(name) -> Generator[None, Any, None]:
    try:
        yield
    except exceptions.BackendError as exc:
        logger.error("Backend (%s) initialization error: %s", name, exc)
    except exceptions.FrontendError as exc:
        logger.error("Frontend (%s) initialization error: %s", name, exc)
    except exceptions.MixerError as exc:
        logger.error("Mixer (%s) initialization error: %s", name, exc)
    except Exception:
        logger.exception("Got un-handled exception from %s", name)


# TODO: move out of this utility class
class RootCommand(Command):
    def __init__(self) -> None:
        super().__init__()
        self.set(base_verbosity_level=0)
        self.add_argument(
            "-h",
            "--help",
            action="help",
            help="Show this message and exit",
        )
        self.add_argument(
            "--version",
            action="version",
            version=f"Mopidy {mopidy.__version__}",
        )
        self.add_argument(
            "-q",
            "--quiet",
            action="store_const",
            const=-1,
            dest="verbosity_level",
            help="less output (warning level)",
        )
        self.add_argument(
            "-v",
            "--verbose",
            action="count",
            dest="verbosity_level",
            default=0,
            help="more output (repeat up to 4 times for even more)",
        )
        self.add_argument(
            "--config",
            action="store",
            dest="config_files",
            type=config_files_type,
            metavar="FILES",
            help="config files to use, colon separated, later files override",
        )
        self.add_argument(
            "-o",
            "--option",
            action="append",
            dest="config_overrides",
            type=config_override_type,
            metavar="OPTIONS",
            help="`section/key=value` values to override config options",
        )

    def run(
        self,
        args: argparse.Namespace,
        config: config_lib.Config,
        *_args: Any,
        **_kwargs: Any,
    ) -> int:
        def on_sigterm(loop) -> bool:
            logger.info("GLib mainloop got SIGTERM. Exiting...")
            loop.quit()
            return GLib.SOURCE_REMOVE

        loop = GLib.MainLoop()
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, on_sigterm, loop)

        mixer_class = self.get_mixer_class(config, args.registry["mixer"])
        backend_classes: list[type[BackendActor]] = args.registry["backend"]
        frontend_classes: list[type[ThreadingActor]] = args.registry["frontend"]
        core = None

        exit_status_code = 0
        try:
            mixer = None
            if mixer_class is not None:
                mixer = self.start_mixer(config, mixer_class)
            if mixer:
                self.configure_mixer(config, mixer)
            audio = self.start_audio(config, mixer)
            backends = self.start_backends(config, backend_classes, audio)
            core = self.start_core(config, mixer, backends, audio)
            self.start_frontends(config, frontend_classes, core)
            logger.info("Starting GLib mainloop")
            loop.run()
        except (
            exceptions.BackendError,
            exceptions.FrontendError,
            exceptions.MixerError,
        ):
            logger.info("Initialization error. Exiting...")
            exit_status_code = 1
        except KeyboardInterrupt:
            logger.info("Interrupted. Exiting...")
        except Exception:
            logger.exception("Uncaught exception")
        finally:
            loop.quit()
            self.stop_frontends(frontend_classes)
            self.stop_core(core)
            self.stop_backends(backend_classes)
            self.stop_audio()
            if mixer_class is not None:
                self.stop_mixer(mixer_class)
            process.stop_remaining_actors()
        return exit_status_code

    def get_mixer_class(
        self,
        config: config_lib.Config,
        mixer_classes: list[type[MixerActor]],
    ) -> type[MixerActor] | None:
        logger.debug(
            "Available Mopidy mixers: %s",
            ", ".join(m.__name__ for m in mixer_classes) or "none",
        )

        if config["audio"]["mixer"] == "none":
            logger.debug("Mixer disabled")
            return None

        selected_mixers = [
            m for m in mixer_classes if m.name == config["audio"]["mixer"]
        ]
        if len(selected_mixers) != 1:
            logger.error(
                'Did not find unique mixer "%s". Alternatives are: %s',
                config["audio"]["mixer"],
                ", ".join(m.name for m in mixer_classes) + ", none" or "none",
            )
            process.exit_process()
        return selected_mixers[0]

    def start_mixer(
        self,
        config: config_lib.Config,
        mixer_class: type[MixerActor],
    ) -> MixerProxy | None:
        logger.info("Starting Mopidy mixer: %s", mixer_class.__name__)
        with _actor_error_handling(mixer_class.__name__):
            mixer = cast(MixerProxy, mixer_class.start(config=config).proxy())
            try:
                mixer.ping().get()
            except pykka.ActorDeadError as exc:
                logger.error("Actor died: %s", exc)
            else:
                return mixer
        return None

    def configure_mixer(
        self,
        config: config_lib.Config,
        mixer: MixerProxy,
    ) -> None:
        volume = config["audio"]["mixer_volume"]
        if volume is not None:
            mixer.set_volume(Percentage(volume))
            logger.info("Mixer volume set to %d", volume)
        else:
            logger.debug("Mixer volume left unchanged")

    def start_audio(
        self,
        config: config_lib.Config,
        mixer: MixerProxy | None,
    ) -> AudioProxy:
        logger.info("Starting Mopidy audio")
        return cast(AudioProxy, Audio.start(config=config, mixer=mixer).proxy())

    def start_backends(
        self,
        config: config_lib.Config,
        backend_classes: list[type[BackendActor]],
        audio,
    ) -> list[BackendProxy]:
        logger.info(
            "Starting Mopidy backends: %s",
            ", ".join(b.__name__ for b in backend_classes) or "none",
        )

        backends = []
        for backend_class in backend_classes:
            with (
                _actor_error_handling(backend_class.__name__),
                timer.time_logger(backend_class.__name__),
            ):
                backend = cast(
                    BackendProxy,
                    backend_class.start(config=config, audio=audio).proxy(),
                )
                backends.append(backend)

        # Block until all on_starts have finished, letting them run in parallel
        for backend in backends[:]:
            try:
                backend.ping().get()
            except pykka.ActorDeadError as exc:
                backends.remove(backend)
                logger.error("Actor died: %s", exc)

        return backends

    def start_core(
        self,
        config: config_lib.Config,
        mixer: MixerProxy | None,
        backends: list[BackendProxy],
        audio: AudioProxy,
    ) -> CoreProxy:
        logger.info("Starting Mopidy core")
        core = cast(
            CoreProxy,
            Core.start(
                config=config,
                mixer=mixer,
                backends=backends,
                audio=audio,
            ).proxy(),
        )
        call = ProxyCall(attr_path=("_setup",), args=(), kwargs={})
        core.actor_ref.ask(call, block=True)
        return core

    def start_frontends(
        self,
        config: config_lib.Config,
        frontend_classes: list[type[ThreadingActor]],
        core: CoreProxy,
    ) -> None:
        logger.info(
            "Starting Mopidy frontends: %s",
            ", ".join(f.__name__ for f in frontend_classes) or "none",
        )

        for frontend_class in frontend_classes:
            with (
                _actor_error_handling(frontend_class.__name__),
                timer.time_logger(frontend_class.__name__),
            ):
                frontend_class.start(config=config, core=core)

    def stop_frontends(self, frontend_classes: list[type[ThreadingActor]]) -> None:
        logger.info("Stopping Mopidy frontends")
        for frontend_class in frontend_classes:
            process.stop_actors_by_class(frontend_class)

    def stop_core(self, core: CoreProxy | None) -> None:
        logger.info("Stopping Mopidy core")
        if core is not None:
            call = ProxyCall(attr_path=("_teardown",), args=(), kwargs={})
            core.actor_ref.ask(call, block=True)
        process.stop_actors_by_class(Core)

    def stop_backends(self, backend_classes: list[type[BackendActor]]) -> None:
        logger.info("Stopping Mopidy backends")
        for backend_class in backend_classes:
            process.stop_actors_by_class(backend_class)

    def stop_audio(self) -> None:
        logger.info("Stopping Mopidy audio")
        process.stop_actors_by_class(Audio)

    def stop_mixer(self, mixer_class: type[MixerActor]) -> None:
        logger.info("Stopping Mopidy mixer")
        process.stop_actors_by_class(mixer_class)


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
        errors: config_lib.ConfigErrors,
        schemas: config_lib.ConfigSchemas,
        **_kwargs: Any,
    ) -> int:
        data = config_lib.format(config, schemas, errors)

        # Throw away all bytes that are not valid UTF-8 before printing
        data = data.encode(errors="surrogateescape").decode(errors="replace")

        print(data)  # noqa: T201
        return 0


class DepsCommand(Command):
    help = "Show dependencies and debug information."

    def __init__(self) -> None:
        super().__init__()
        self.set(base_verbosity_level=-1)

    def run(
        self,
        args: argparse.Namespace,  # noqa: ARG002
        config: config_lib.Config,  # noqa: ARG002
        *_args: Any,
        **_kwargs: Any,
    ) -> int:
        print(deps.format_dependency_list())  # noqa: T201
        return 0
