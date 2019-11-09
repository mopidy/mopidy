import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall('__([a-z]+)__ = "([^"]+)"', fh.read()))
        return metadata["version"]


DOCS_DEPS = ["pygraphviz", "sphinx", "sphinx_rtd_theme"]
LINT_DEPS = [
    "black",
    "check-manifest",
    "flake8",
    "flake8-bugbear",
    "flake8-import-order",
    "isort[pyproject]",
    "pep8-naming",
]
RELEASE_DEPS = ["invoke", "twine", "wheel"]
TEST_DEPS = ["pytest", "pytest-cov", "responses"]
DEV_DEPS = DOCS_DEPS + LINT_DEPS + RELEASE_DEPS + TEST_DEPS


setup(
    name="Mopidy",
    version=get_version("mopidy/__init__.py"),
    url="https://mopidy.com/",
    license="Apache License, Version 2.0",
    author="Stein Magnus Jodal",
    author_email="stein.magnus@jodal.no",
    description="Mopidy is an extensible music server written in Python",
    long_description=open("README.rst").read(),
    packages=find_packages(exclude=["tests", "tests.*"]),
    zip_safe=False,
    include_package_data=True,
    python_requires=">= 3.7",
    install_requires=[
        "Pykka >= 2.0.1",
        "requests >= 2.0",
        "setuptools",
        "tornado >= 4.4",
    ],
    extras_require={
        "http": [],  # Keep for backwards compat
        "docs": DOCS_DEPS,
        "lint": LINT_DEPS,
        "test": TEST_DEPS,
        "dev": DEV_DEPS,
    },
    entry_points={
        "console_scripts": ["mopidy = mopidy.__main__:main"],
        "mopidy.ext": [
            "http = mopidy.http:Extension",
            "file = mopidy.file:Extension",
            "m3u = mopidy.m3u:Extension",
            "mpd = mopidy.mpd:Extension",
            "softwaremixer = mopidy.softwaremixer:Extension",
            "stream = mopidy.stream:Extension",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],
)
