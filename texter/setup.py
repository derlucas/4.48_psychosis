#!/usr/bin/python
# -*- coding: utf-8 -*-

from distribute_setup import use_setuptools
use_setuptools()

import sys
from setuptools import find_packages, setup

if sys.version_info >= (3,):
    extras['use_2to3'] = True

setup(
    name='texter',
    version="0.1",
    packages=find_packages(exclude=["scripts",]),

    include_package_data = True,

    package_data = {
        "texter" :  ["*.ui", "*.qrc", "*.png", "*.ico", "*.html"]},

    exclude_package_data = {'': ['.gitignore']},

    #install_requires=[],
    data_files=[
        ('/usr/share/applications', ['texter/texter.desktop']),
        ('/usr/share/icons/hicolor/32x32/apps/texter_icon.png', ['texter/icon.png'])],

    # installing unzipped
    zip_safe = False,

    # predefined extension points, e.g. for plugins
    entry_points = """
    [console_scripts]
    texter = texter.main:main
    """,
    # pypi metadata
    author = "Stefan Kögl",

    # FIXME: add author email
    author_email = "hotte@ctdo.de",
    description = "live text tool",

    # FIXME: add long_description
    long_description = """
    """,

    # FIXME: add license
    license = "GPL",

    # FIXME: add keywords
    keywords = "",

    # FIXME: add download url
    url = "",
    test_suite='tests'
)
