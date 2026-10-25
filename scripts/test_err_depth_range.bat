@echo off
cd /d "%~dp0.."
python src\main.py --package Serilog --version 1.0.0 --max-depth 99
