#!/usr/bin/python
# -*- coding: utf-8 -*-

from distribute_setup import use_setuptools
use_setuptools()

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
    ekg2osc = sensors2osc.ekg2osc:main
    ekgmerle = sensors2osc.ekg2osc:main
    ekguwe = sensors2osc.ekg2osc:main
    ekgbjoern = sensors2osc.ekg2osc:main
    pulse2osc = sensors2osc.pulse2osc:main
    pulsemerle = sensors2osc.pulse2osc:main
    pulseuwe = sensors2osc.pulse2osc:main
    pulsebjoern = sensors2osc.pulse2osc:main
    ehealth2osc = sensors2osc.ehealth2osc:main
    ehealthmerle = sensors2osc.ehealth2osc:main
    ehealthuwe = sensors2osc.ehealth2osc:main
    ehealthbjoern = sensors2osc.ehealth2osc:main
    """,
    # pypi metadata
    author = "Stefan Kögl",

    # FIXME: add author email
    author_email = "hotte@ctdo.de",
    description = "tools for sending osc messages from olimex and ehealth biofeedback platforms to OSC",

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
