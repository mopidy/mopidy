from __future__ import annotations

import contextlib
import logging
from collections.abc import Generator
from typing import cast

import pykka
from pykka import ThreadingActor
from pykka.messages import ProxyCall

from mopidy import exceptions
from mopidy._app import process
from mopidy._app.extensions import ExtensionManager, ExtensionStatus
from mopidy._lib import gi, logs
from mopidy._lib.process import exit_process
from mopidy.audio import AudioProxy, GstAudio
from mopidy.backend import BackendActor, BackendProxy
from mopidy.config import Config
from mopidy.core import Core, CoreProxy
from mopidy.ext import Registry
from mopidy.mixer import MixerActor, MixerProxy
from mopidy.types import Percentage

logger = logging.getLogger(__name__)


def command() -> int:
    # Get config and extensions prepared by the CLI layer before calling us.
    config = Config.get_global()
    extensions = ExtensionManager.get_global()

    registry = Registry()
    for ext_name, record in extensions.with_status(ExtensionStatus.ENABLED).items():
        assert record.extension
        try:
            record.extension.setup(registry)
        except Exception:
            logger.exception(
                f"Extension {ext_name} failed during setup. "
                "This might have left the registry in a bad state."
            )

    loop = gi.create_glib_loop()

    mixer_classes = cast(list[type[MixerActor]], registry["mixer"])
    mixer_class = get_mixer_class(config, mixer_classes)
    backend_classes = cast(list[type[BackendActor]], registry["backend"])
    frontend_classes = cast(list[type[ThreadingActor]], registry["frontend"])
    core = None

    exit_status_code = 0
    try:
        mixer = None
        if mixer_class is not None:
            mixer = start_mixer(config, mixer_class)
        if mixer:
            configure_mixer(config, mixer)
        audio = start_audio(config, mixer)
        backends = start_backends(config, backend_classes, audio)
        core = start_core(config, mixer, backends, audio)
        start_frontends(config, frontend_classes, core)
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
        stop_frontends(frontend_classes)
        stop_core(core)
        stop_backends(backend_classes)
        stop_audio()
        if mixer_class is not None:
            stop_mixer(mixer_class)
        process.stop_remaining_actors()
    return exit_status_code


def get_mixer_class(
    config: Config,
    mixer_classes: list[type[MixerActor]],
) -> type[MixerActor] | None:
    logger.debug(
        "Available Mopidy mixers: %s",
        ", ".join(m.__name__ for m in mixer_classes) or "none",
    )

    if config["audio"]["mixer"] == "none":
        logger.debug("Mixer disabled")
        return None

    selected_mixers = [m for m in mixer_classes if m.name == config["audio"]["mixer"]]
    if len(selected_mixers) != 1:
        logger.error(
            'Did not find unique mixer "%s". Alternatives are: %s',
            config["audio"]["mixer"],
            ", ".join(m.name for m in mixer_classes) + ", none" or "none",
        )
        exit_process()
    return selected_mixers[0]


def start_mixer(
    config: Config,
    mixer_class: type[MixerActor],
) -> MixerProxy | None:
    logger.info("Starting Mopidy mixer: %s", mixer_class.__name__)
    with actor_error_handling(mixer_class.__name__):
        mixer = cast(MixerProxy, mixer_class.start(config=config).proxy())
        try:
            mixer.ping().get()
        except pykka.ActorDeadError as exc:
            logger.error("Actor died: %s", exc)
        else:
            return mixer
    return None


def configure_mixer(
    config: Config,
    mixer: MixerProxy,
) -> None:
    volume = config["audio"]["mixer_volume"]
    if volume is not None:
        mixer.set_volume(Percentage(volume))
        logger.info("Mixer volume set to %d", volume)
    else:
        logger.debug("Mixer volume left unchanged")


def start_audio(
    config: Config,
    mixer: MixerProxy | None,
) -> AudioProxy:
    logger.info("Starting Mopidy audio")
    return cast(AudioProxy, GstAudio.start(config=config, mixer=mixer).proxy())


def start_backends(
    config: Config,
    backend_classes: list[type[BackendActor]],
    audio: AudioProxy,
) -> list[BackendProxy]:
    logger.info(
        "Starting Mopidy backends: %s",
        ", ".join(b.__name__ for b in backend_classes) or "none",
    )

    backends = []
    for backend_class in backend_classes:
        with (
            actor_error_handling(backend_class.__name__),
            logs.log_time_spent(backend_class.__name__),
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
    config: Config,
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
    config: Config,
    frontend_classes: list[type[ThreadingActor]],
    core: CoreProxy,
) -> None:
    logger.info(
        "Starting Mopidy frontends: %s",
        ", ".join(f.__name__ for f in frontend_classes) or "none",
    )

    for frontend_class in frontend_classes:
        with (
            actor_error_handling(frontend_class.__name__),
            logs.log_time_spent(frontend_class.__name__),
        ):
            frontend_class.start(config=config, core=core)


def stop_frontends(frontend_classes: list[type[ThreadingActor]]) -> None:
    logger.info("Stopping Mopidy frontends")
    for frontend_class in frontend_classes:
        process.stop_actors_by_class(frontend_class)


def stop_core(core: CoreProxy | None) -> None:
    logger.info("Stopping Mopidy core")
    if core is not None:
        call = ProxyCall(attr_path=("_teardown",), args=(), kwargs={})
        core.actor_ref.ask(call, block=True)
    process.stop_actors_by_class(Core)


def stop_backends(backend_classes: list[type[BackendActor]]) -> None:
    logger.info("Stopping Mopidy backends")
    for backend_class in backend_classes:
        process.stop_actors_by_class(backend_class)


def stop_audio() -> None:
    logger.info("Stopping Mopidy audio")
    process.stop_actors_by_class(GstAudio)


def stop_mixer(mixer_class: type[MixerActor]) -> None:
    logger.info("Stopping Mopidy mixer")
    process.stop_actors_by_class(mixer_class)


@contextlib.contextmanager
def actor_error_handling(name: str) -> Generator[None]:
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
