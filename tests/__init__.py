#!/usr/bin/env python
from setuptools import setup, find_packages

TEST_REQUIRES = [
    'coverage',
    'flexmock',
    'nose',
    'unittest2',
]

INSTALL_REQUIRES = [
]

SCRIPTS = ['backup.py', 'bitbucket-backup']

setup(
    name='cosential-compass',
    version='0.0.1',
    author='NOVO Construction',
    author_email='skuehn@novoconstruction.com',
    url='https://github.com/NOVO-Construction/cosential-compass',
    description='Python client for Cosential Compass',
    long_description=__doc__,
    packages=find_packages(exclude=('tests', 'tests.*',)),
    scripts=SCRIPTS,
    zip_safe=False,
    extras_require={
        'tests': TEST_REQUIRES,
    },
    license='BSD',
    tests_require=TEST_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    test_suite='tests',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python',
    ],
)
