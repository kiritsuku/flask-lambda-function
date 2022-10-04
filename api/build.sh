#!/bin/sh

# exit when any command fails
set -e

# Download dependencies
pip install --upgrade -r requirements.txt -t ./package
