from __future__ import unicode_literals

import re

from setuptools import setup, find_packages


def get_version(filename):
    init_py = open(filename).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
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
        'setuptools',
        'Pykka >= 1.1',
    ],
    extras_require={
        'http': ['cherrypy >= 3.2.2', 'ws4py >= 0.2.3'],
    },
    test_suite='nose.collector',
    tests_require=[
        'nose',
        'mock >= 1.0',
    ],
    entry_points={
        'console_scripts': [
            'mopidy = mopidy.__main__:main',
            'mopidy-scan = mopidy.scanner:main',
            'mopidy-convert-config = mopidy.config.convert:main',
        ],
        'mopidy.ext': [
            'http = mopidy.frontends.http:Extension [http]',
            'local = mopidy.backends.local:Extension',
            'mpd = mopidy.frontends.mpd:Extension',
            'stream = mopidy.backends.stream:Extension',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
