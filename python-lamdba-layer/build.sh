#!/bin/sh

# exit when any command fails
set -e

# Download dependencies
pip install --upgrade -r requirements.txt -t ./package

# Package all dependencies and sources to a lambda layer
# Instructions for python lambda layers: https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html
DIR=./__pycache__/lambda-layer/python/
rm -rf "$DIR"
mkdir -p "$DIR"
cp -R ./*.py "$DIR"
cp -R ./package/* "$DIR"
