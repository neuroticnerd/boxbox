#! /usr/bin/env python
# -*- coding: utf-8 -*-

# see this link for easily setting up an installable Python package
# http://gehrcke.de/2014/02/distributing-a-python-command-line-application/
import re
from setuptools import setup, find_packages


def fread(filename, split=False, keepnl=False):
    """
    may raise IOError exceptions from file operations
    """
    result = ""
    if split:
        result = []
    with open(filename, 'rb') as f:
        # use readme.read().decode("utf-8") instead?
        for line in f:
            tmpline = line
            if line == '\n':
                continue
            if split:
                if '#' in tmpline.strip()[:2]:
                    continue
                result.append(line.replace('\n', ''))
            else:
                result += line
    return result


with open('boxbox/__init__.py', 'rb') as finit:
    findver = re.compile(r'^\s*__version__\s*=\s*"(.*)"', re.M)
    VERSION = findver.search(finit.read()).group(1)

PROJECT = "boxbox"
AUTHOR = "Bryce Eggleton"
EMAIL = "eggleton.bryce@gmail.com"
DESC = "Vagrant + VirtualBox utilities"
LONG_DESC = fread('README.rst')
LICENSE = fread('LICENSE')
URL = "https://github.com/neuroticnerd/boxbox"
REQUIRES = fread('requirements', True)
SCRIPTS = {"console_scripts": ['boxbox = boxbox.boxbox:CLI']}

setup(
    name = PROJECT,
    url = URL,
    author = AUTHOR,
    author_email = EMAIL,
    version = VERSION,
    description = DESC,
    long_description = LONG_DESC,
    license=LICENSE,
    packages = find_packages(include=["boxbox"]),
    entry_points = SCRIPTS,
    install_requires=REQUIRES,
    )

# @@@ TODO: figure out if there's a way to use setup() to enable tab complete
# for bash (eval "$(_FOO_BAR_COMPLETE=source foo-bar)")
