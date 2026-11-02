#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package A --test-repo --repo examples/chain.txt --max-depth 2
