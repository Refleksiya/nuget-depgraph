#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package Microsoft.Extensions.Logging --version 8.0.0
