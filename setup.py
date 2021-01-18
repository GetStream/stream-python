#!/usr/bin/env python


from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from stream import __version__, __maintainer__, __email__, __license__
import sys

tests_require = ["pytest", "unittest2", "pytest-cov", "python-dateutil"]
ci_require = ["black", "flake8", "pytest-cov"]

long_description = open("README.md", "r").read()

install_requires = [
    "pycryptodomex>=3.8.1,<4",
    "requests>=2.3.0,<3",
    "pyjwt>=2.0.0,<3",
    "pytz>=2019.3",
]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(["-v", "--cov=./"])
        sys.exit(errno)


setup(
    name="stream-python",
    version=__version__,
    author=__maintainer__,
    author_email=__email__,
    url="http://github.com/GetStream/stream-python",
    description="Client for getstream.io. Build scalable newsfeeds & activity streams in a few hours instead of weeks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=__license__,
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={"test": tests_require, "ci": ci_require},
    cmdclass={"test": PyTest},
    tests_require=tests_require,
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
