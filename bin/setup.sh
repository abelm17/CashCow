#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
VENV_DIR="$BACKEND/.venv"
REQUIREMENTS="$BACKEND/requirements.txt"

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Error: Python 3 is required." >&2
    exit 1
fi

if ! "$PYTHON" -c \
    'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
then
    echo "Error: Python 3.10 or newer is required." >&2
    exit 1
fi

if ! "$PYTHON" -c 'import venv' >/dev/null 2>&1; then
    echo "Error: Python's venv module is required." >&2
    exit 1
fi

if [[ ! -f "$REQUIREMENTS" ]]; then
    echo "Error: backend/requirements.txt is missing." >&2
    exit 1
fi

if [[ -f "$ROOT/frontend/package.json" ]]; then
    for tool in node npm; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "Error: $tool is required for the frontend." >&2
            exit 1
        fi
    done

    if [[ ! -f "$ROOT/frontend/package-lock.json" ]]; then
        echo "Error: frontend/package-lock.json is missing." >&2
        exit 1
    fi
fi

echo "Prerequisites checked."

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

if [[ -x "$VENV_DIR/Scripts/python.exe" ]]; then
    VENV_PYTHON="$VENV_DIR/Scripts/python.exe"
elif [[ -x "$VENV_DIR/bin/python" ]]; then
    VENV_PYTHON="$VENV_DIR/bin/python"
else
    echo "Error: Virtual environment is incomplete: $VENV_DIR" >&2
    exit 1
fi

echo "Installing backend dependencies..."
if ! "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
    echo "Error: pip is missing from the virtual environment." >&2
    exit 1
fi
"$VENV_PYTHON" -m pip install -r "$REQUIREMENTS"

if [[ -f "$ROOT/.env" ]]; then
    echo ".env already exists."
else
    if [[ -f "$ROOT/.env.example" ]]; then
        cp "$ROOT/.env.example" "$ROOT/.env"
        echo "Created .env from .env.example. Fill in its values."
    else
        touch "$ROOT/.env"
        echo "Created empty .env. Fill in required values."
    fi
fi

if [[ -f "$ROOT/frontend/package.json" ]]; then
    echo "Installing frontend dependencies..."
    (cd "$ROOT/frontend" && npm ci)
fi

echo "Setup complete."