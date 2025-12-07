from __future__ import annotations

import argparse
import contextlib
import logging
import signal
from collections.abc import Generator
from typing import (
    Any,
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
from mopidy.commands import Command, config_files_type, config_override_type
from mopidy.core import Core, CoreProxy
from mopidy.internal import process, timer
from mopidy.internal.gi import GLib
from mopidy.mixer import MixerActor, MixerProxy
from mopidy.types import Percentage

logger = logging.getLogger(__name__)


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


@contextlib.contextmanager
def _actor_error_handling(name) -> Generator[None]:
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
