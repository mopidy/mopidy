from __future__ import absolute_import, unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy',
    version=get_version('mopidy/__init__.py'),
    url='http://www.mopidy.com/',
    license='Apache License, Version 2.0',
    author='Stein Magnus Jodal',
    author_email='stein.magnus@jodal.no',
    description='Music server with MPD and Spotify support',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'Pykka >= 1.1',
        'requests >= 2.0',
        'setuptools',
        'tornado >= 3.2',
    ],
    extras_require={'http': []},
    entry_points={
        'console_scripts': [
            'mopidy = mopidy.__main__:main',
        ],
        'mopidy.ext': [
            'http = mopidy.http:Extension',
            'local = mopidy.local:Extension',
            'file = mopidy.file:Extension',
            'm3u = mopidy.m3u:Extension',
            'mpd = mopidy.mpd:Extension',
            'softwaremixer = mopidy.softwaremixer:Extension',
            'stream = mopidy.stream:Extension',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
