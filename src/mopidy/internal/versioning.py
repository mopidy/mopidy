import subprocess
from pathlib import Path

import mopidy


def get_version():
    try:
        return get_git_version()
    except OSError:
        return mopidy.__version__


def get_git_version():
    project_dir = Path(mopidy.__file__).parent.parent.resolve()
    process = subprocess.Popen(
        ["git", "describe"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=project_dir,
    )
    if process.wait() != 0:
        raise OSError('Execution of "git describe" failed')
    assert process.stdout
    version = process.stdout.read().strip().decode()
    if version.startswith("v"):
        version = version[1:]
    return version
