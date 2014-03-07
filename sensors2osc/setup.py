#!/usr/bin/python
# -*- coding: utf-8 -*-

from distribute_setup import use_setuptools
use_setuptools()

from scripts.version import get_git_version
import sys
from setuptools import find_packages, setup

if sys.version_info >= (3,):
    extras['use_2to3'] = True

setup(
    name='sensors2osc',
    version="0.1",
    packages=find_packages(exclude=["scripts",]),

    include_package_data = True,

    package_data = {
        "chaosc" :  ["config/*",]},

    exclude_package_data = {'': ['.gitignore']},

    install_requires=[
        "pyserial",],

    # installing unzipped
    zip_safe = False,

    # predefined extension points, e.g. for plugins
    entry_points = """
    [console_scripts]
    sensors2osc = sensors2osc.main:main
    """,
    # pypi metadata
    author = "Stefan Kögl",

    # FIXME: add author email
    author_email = "",
    description = "osc filtering application level gateway",

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
