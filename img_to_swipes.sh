#!/usr/bin/env sh
set -e

if ! command -v uv >/dev/null 2>&1; then
    echo "UV is not installed"
    echo "Please follow the installation instructions: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

uv run img_to_swipes.py
