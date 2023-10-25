#!/usr/bin/env python


from setuptools import setup, find_packages
from stream import __version__, __maintainer__, __email__, __license__

install_requires = [
    "requests>=2.31.0,<3",
    "pyjwt>=2.8.0,<3",
    "pytz>=2023.3.post1",
    "aiohttp>=3.9.0b0",
]
tests_require = ["pytest", "pytest-cov", "python-dateutil", "pytest-asyncio"]
ci_require = ["black", "flake8", "pytest-cov"]

long_description = open("README.md", "r").read()

setup(
    name="stream-python",
    version=__version__,
    author=__maintainer__,
    author_email=__email__,
    url="http://github.com/GetStream/stream-python",
    description="Client for getstream.io. Build scalable newsfeeds & activity streams in a few hours instead of weeks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        "Bug Tracker": "https://github.com/GetStream/stream-python/issues",
        "Documentation": "https://getstream.io/activity-feeds/docs/python/?language=python",
        "Release Notes": "https://github.com/GetStream/stream-python/releases/tag/v{}".format(
            __version__
        ),
    },
    license=__license__,
    packages=find_packages(exclude=["*tests*"]),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={"test": tests_require, "ci": ci_require},
    tests_require=tests_require,
    include_package_data=True,
    python_requires=">=3.7",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
