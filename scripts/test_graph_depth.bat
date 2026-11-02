@echo off
cd /d "%~dp0.."
python src\main.py --package A --test-repo --repo examples/chain.txt --max-depth 2
