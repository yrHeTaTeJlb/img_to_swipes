#!/usr/bin/env sh
set -e

if ! command -v uv >/dev/null 2>&1; then
    pip install uv
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "Failed to install UV"
    echo "Please install it manually: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

uv run img_to_swipes.py
