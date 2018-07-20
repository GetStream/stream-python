#!/usr/bin/env python


from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from stream import __version__, __maintainer__, __email__, __license__
import sys

unit = 'unittest2py3k' if sys.version_info > (3, 0, 0) else 'unittest2'
tests_require = [
    unit,
    'pytest==3.2.5',
    'unittest2',
    'pytest-cov',
    'python-dateutil'
]

long_description = open('README.md', 'r').read()

requests = 'requests>=2.3.0,<3'

if sys.version_info < (2, 7, 9):
    requests = 'requests[security]>=2.4.1,<3'

install_requires = [
    'pycryptodomex==3.4.7',
    requests,
    'six>=1.8.0'
]

if sys.version_info < (2, 7, 0):
    install_requires.append('pyOpenSSL<18.0.0')
    install_requires.append('pyjwt>=1.3.0,<1.6.0')
else:
    install_requires.append('pyjwt>=1.3.0,<1.7.0')


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(
            '-v --cov=./')
        sys.exit(errno)


setup(
    name='stream-python',
    version=__version__,
    author=__maintainer__,
    author_email=__email__,
    url='http://github.com/GetStream/stream-python',
    description='Client for getstream.io. Build scalable newsfeeds & activity streams in a few hours instead of weeks.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license=__license__,
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
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
