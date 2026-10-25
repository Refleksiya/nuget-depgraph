#!/bin/sh
cd "$(dirname "$0")/.."
python3 src/main.py --package Serilog --version 1.0.0 --repo nuget.org
