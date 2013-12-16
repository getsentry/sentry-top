#!/usr/bin/env python
"""
sentry-top
==========

An extension for Sentry which allows you to track the most active projects ala ``top``

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: Apache License 2.0, see LICENSE for more details.
"""
from setuptools import setup, find_packages


tests_require = [
    'exam',
    'mock',
    'pytest',
    'pytest-django',
    'unittest2',
]

install_requires = [
    'nydus',
    'redis',
    'sentry>=5.0.0',
]

setup(
    name='sentry-top',
    version='0.1.0',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/getsentry/sentry-top',
    description='A Sentry extension which tracks the most active projects',
    long_description=__doc__,
    license='Apache License 2.0',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='runtests.runtests',
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'top = sentry_top',
        ],
        'sentry.plugins': [
            'top = sentry_top.plugin:TopPlugin'
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
