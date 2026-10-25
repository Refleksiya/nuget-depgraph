#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package "bad name" --version 1.0.0
