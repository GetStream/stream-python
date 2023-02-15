#!/usr/bin/env bash

set -e

if ! black stream --check -q; then
    black stream
    echo
    echo "some files were not formatted correctly (black) commit aborted!"
    echo "your changes are still staged, you can accept formatting changes with git add or ignore them by adding --no-verify to git commit"
    exit 1
fi

if ! flake8 --ignore=E501,E225,W293,W503,F401 stream; then
    echo
    echo "commit is aborted because there are some error prone issues in your changes as printed above"
    echo "your changes are still staged, you can accept formatting changes with git add or ignore them by adding --no-verify to git commit"
    exit 1
fi
