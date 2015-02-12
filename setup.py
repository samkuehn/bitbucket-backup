#!/usr/bin/env python
from setuptools import find_packages, setup

TEST_REQUIRES = [
    'nose',
    'unittest2',
]

INSTALL_REQUIRES = [
]
try:
    import argparse  # noqa
except ImportError:
    INSTALL_REQUIRES.append('argparse')

SCRIPTS = ['backup.py', 'bitbucket-backup']

setup(
    name='bitbucket-backup',
    version='0.0.1',
    author='Sam Kuehn',
    author_email='samkuehn@gmail.com',
    url='https://github.com/samkuehn/bitbucket-backup',
    description='Python script to backup Bitbucket repos',
    long_description=__doc__,
    packages=find_packages(exclude=('tests', 'tests.*',)),
    scripts=SCRIPTS,
    zip_safe=False,
    extras_require={
        'tests': TEST_REQUIRES,
    },
    tests_require=TEST_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    test_suite='tests',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administrationt',
        'Programming Language :: Python',
    ],
)
