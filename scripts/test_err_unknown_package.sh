#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package NoSuchPackage.Example --version 1.0.0
