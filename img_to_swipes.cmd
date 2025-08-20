@echo off

where uv >NUL 2>&1
if errorlevel 1 (
    pip install uv
)

where uv >NUL 2>&1
if errorlevel 1 (
    echo Failed to install UV
    echo Please install it manually: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

uv run img_to_swipes.py
