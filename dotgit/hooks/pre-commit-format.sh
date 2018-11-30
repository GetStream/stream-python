#!/usr/bin/env bash

set -e

if ! black . --check -q; then
    black .
    echo "some files were not formatted correctly (black) commit aborted!"
    echo "your changes are still staged, you can accept formatting changes with git add or ignore them by adding --no-verify to git commit"
    exit 1
fi

flake8

