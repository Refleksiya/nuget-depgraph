#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package X --test-repo --repo examples/simple.txt
