#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package A --test-repo --repo examples/bad_name.txt
