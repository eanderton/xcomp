#!/bin/bash

export PYTEST_ADDOPTS="--color=yes"
pytest --cov=xcomp --cov-report html tests/*.py  "$@"

