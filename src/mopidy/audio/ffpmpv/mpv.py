from __future__ import annotations

import contextlib
import json
import logging
import pathlib
import socket
import subprocess
import tempfile
import time
from functools import cache
from typing import Any

logger = logging.getLogger(__name__)


@cache  # cache means there'll be one tempdir of this per process
def get_control_dir_path() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="mpvc"))


class MpvError(RuntimeError):
    def __init__(self, message, *, data):
        super().__init__(message)
        self.data = data


class Mpv:
    def __init__(self) -> None:
        self.uri: str | None = None
        self.process: subprocess.Popen | None = None
        self.ipc_socket_path: pathlib.Path | None = None

    def close(self):
        if self.process:
            self.process.terminate()
            self.process = None
        if self.ipc_socket_path:
            with contextlib.suppress(Exception):
                self.ipc_socket_path.unlink()
            self.ipc_socket_path = None
        self.uri = None

    def play(self, uri):
        if self.uri == uri:
            self.unpause()
            return

        # TODO: this could do something more elegant than kill the mpv and restart it
        #       when changing tracks (see the `loadfile` command), but this is a POC.

        self.close()
        ipc_socket_path = get_control_dir_path() / f"{int(time.time()):x}.sock"
        if len(str(self.ipc_socket_path)) > 100:
            msg = "IPC socket path too long"
            raise RuntimeError(msg)
        logger.info("IPC socket: %s", ipc_socket_path)
        args = [
            "mpv",
            "--no-video",
            f"--input-ipc-server={ipc_socket_path}",
            uri,
        ]
        # Note these must be assigned to `self` at the end,
        # so as to avoid certain race conditions :melt:
        self.process = subprocess.Popen(args)  # noqa: S603
        self.ipc_socket_path = ipc_socket_path
        self.uri = uri

    @property
    def active(self) -> bool:
        return self.process is not None

    def stop(self):
        self.close()

    def send_message(self, msg: Any):
        assert self.ipc_socket_path
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(str(self.ipc_socket_path))
            logger.info("MPV told: %s", msg)
            sock.sendall(json.dumps(msg).encode("utf-8") + b"\n")
            sock.shutdown(socket.SHUT_WR)
            data = sock.recv(4096)
            ret = json.loads(data)
            logger.debug("MPV says: %s", ret)
            if ret.get("error") != "success":
                msg = f"MPV error: {ret}"
                raise MpvError(msg, data=ret)
        return ret

    def pause(self):
        if self.active:
            self.send_message({"command": ["set_property", "pause", True]})

    def unpause(self):
        if self.active:
            self.send_message({"command": ["set_property", "pause", False]})

    def get_position_seconds(self) -> float | None:
        if self.active:
            ret = self.send_message({"command": ["get_property", "time-pos/full"]})
            return ret["data"]
        return None

    def set_position_seconds(self, position_seconds: float) -> None:
        if self.active:
            self.send_message(
                {"command": ["set_property", "time-pos", position_seconds]}
            )
