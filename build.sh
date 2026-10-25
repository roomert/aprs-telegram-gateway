#!/usr/bin/env sh
# Linux / Raspberry Pi build. Settings live in build.toml.
# Usage: sh ./build.sh [--label LABEL]
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Python 3 was not found. Install python3 and python3-venv, then retry." >&2
        exit 2
    fi
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

"$VENV_PYTHON" -m pip install -q -r "$PROJECT_ROOT/requirements-build.txt"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    "$VENV_PYTHON" -m pip install -q -r "$PROJECT_ROOT/requirements.txt"
fi

exec "$VENV_PYTHON" "$PROJECT_ROOT/build.py" "$@"
