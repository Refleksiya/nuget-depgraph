@echo off
cd /d "%~dp0.."
python src\main.py --package X --test-repo --repo examples/simple.txt
