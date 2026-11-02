@echo off
cd /d "%~dp0.."
python src\main.py --package A --test-repo --repo examples/cycle.txt
