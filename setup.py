#!/usr/bin/env python
# encoding: utf-8

import os

from setuptools import (
    setup,
    find_packages,
)


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


NAME = "django-storage-qcloud"
DESCRIPTION = "Django qcloud cos storage backend"
AUTHOR = "Ford"
AUTHOR_EMAIL = "agile.guo@gmail.com"
URL = "https://github.com/fordguo/django-storage-qcloud"
VERSION = '0.1.1'

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    include_package_data=True,
    license="BSD",
    url=URL,
    packages=find_packages(),
    install_requires=[
        'django',
        'cos-python-sdk-v5',
    ],
    zip_safe=False,
)
