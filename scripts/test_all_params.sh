#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package Serilog --version 3.1.1 --repo https://api.nuget.org/v3-flatcontainer --tree --max-depth 5
