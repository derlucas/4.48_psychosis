#!/usr/bin/python
# -*- coding: utf-8 -*-

from distribute_setup import use_setuptools
use_setuptools()

import sys
from setuptools import find_packages, setup

if sys.version_info >= (3,):
    extras['use_2to3'] = True

setup(
    name='dump_grabber',
    version="0.1",
    packages=find_packages(exclude=["scripts",]),

    include_package_data = True,

    exclude_package_data = {'': ['.gitignore']},

    # installing unzipped
    zip_safe = False,

    # predefined extension points, e.g. for plugins
    entry_points = """
    [console_scripts]
    dump_grabber = dump_grabber.main:main
    """,
    # pypi metadata
    author = "Stefan Kögl",

    # FIXME: add author email
    author_email = "",
    description = "osc messages logging terminal as mjpeg stream, uses 3 columns",

    # FIXME: add long_description
    long_description = """
    """,

    # FIXME: add license
    license = "LGPL",

    # FIXME: add keywords
    keywords = "",

    # FIXME: add download url
    url = "",
    test_suite='tests'
)
