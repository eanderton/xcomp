#!/bin/bash

export PYTEST_ADDOPTS="--color=yes"
pytest --cov=oxeye --cov-report html tests/*.py

