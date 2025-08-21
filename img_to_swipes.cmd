@echo off

where uv >NUL 2>&1
if errorlevel 1 (
    echo UV is not installed
    echo Please follow the installation instructions: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

uv run img_to_swipes.py
