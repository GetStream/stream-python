#!/usr/bin/env python


from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from stream import __version__, __maintainer__, __email__
import sys


unit = 'unittest2py3k' if sys.version_info > (3, 0, 0) else 'unittest2'
tests_require = [
    'pep8',
    unit,
    #'pytest',
    'python-coveralls',
    'unittest2',
    'pytest-cov',
    'python-dateutil'
]

long_description = '''
Documentation
-------------
Full documentation is available on `Github`_.

.. _`Github`: https://github.com/tschellenbach/stream-python
'''

install_requires = [
    'requests>=2.3.0',
]


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(
            'stream/tests.py --cov stream --cov-report term-missing -v')
        sys.exit(errno)

setup(
    name='stream-python',
    version=__version__,
    author=__maintainer__,
    author_email=__email__,
    url='http://github.com/tschellenbach/stream-python',
    description='Client for getstream.io. Build scalable newsfeeds & activity streams in a few hours instead of weeks.',
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={'test': tests_require},
    cmdclass={'test': PyTest},
    tests_require=tests_require,
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
