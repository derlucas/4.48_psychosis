#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from setuptools import find_packages, setup

if sys.version_info >= (3,):
    extras['use_2to3'] = True

setup(
    name='psylib',
    version="0.2",
    packages=find_packages(exclude=["scripts",]),

    include_package_data = True,

    exclude_package_data = {'': ['.gitignore']},

    zip_safe = False,

    # pypi metadata
    author = "Stefan Kögl",

    # FIXME: add author email
    author_email = "hotte@ctdo.de",
    description = "library for psychosis",

    # FIXME: add long_description
    long_description = """
    """,

    # FIXME: add license
    license = "GPL",

    # FIXME: add keywords
    keywords = "",

    # FIXME: add download url
    url = "",
)
