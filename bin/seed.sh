#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
ENV_FILE="$ROOT/.env"
if [[ -x "$BACKEND/.venv/Scripts/python.exe" ]]; then
    VENV_PYTHON="$BACKEND/.venv/Scripts/python.exe"
elif [[ -x "$BACKEND/.venv/bin/python" ]]; then
    VENV_PYTHON="$BACKEND/.venv/bin/python"
else
    echo "Error: Virtual environment missing. Run bin/setup.sh first." >&2
    exit 1
fi
RESET=false
YES=false
for arg in "$@"; do
    case "$arg" in
        --reset) RESET=true ;;
        --yes) YES=true ;;
        *) echo "Error: Unknown option: $arg" >&2; exit 1 ;;
    esac
done
if [[ "$YES" == true && "$RESET" != true ]]; then
    echo "Error: --yes requires --reset." >&2
    exit 1
fi
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: Root .env is missing. Run setup and configure it." >&2
    exit 1
fi
cd "$BACKEND"

"$VENV_PYTHON" - "$ENV_FILE" <<'CHECK_PY_END'
import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text
load_dotenv(sys.argv[1], override=True)
required = ("DATABASE_PASSWORD", "SEED_USER_PASSWORD", "SECRET_KEY")
missing = [key for key in required if not os.environ.get(key)]
if missing:
    print("Error: Missing .env variables: " + ", ".join(missing), file=sys.stderr)
    sys.exit(1)
try:
    from app.database import engine
    async def check():
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        finally:
            await engine.dispose()
    asyncio.run(check())
except Exception:
    print("Error: Cannot connect to PostgreSQL. Check configuration and whether it is running.", file=sys.stderr)
    sys.exit(1)
CHECK_PY_END
if [[ "$RESET" == true && "$YES" != true ]]; then
    echo "WARNING: Reset deletes and recreates demo users, branches, ATMs, jobs and reports."
    read -r -p "Type 'yes' to continue: " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        echo "Reset cancelled."
        exit 0
    fi
fi

"$VENV_PYTHON" - "$ENV_FILE" "$RESET" <<'RUN_PY_END'
import os
import subprocess
import sys
from dotenv import load_dotenv
load_dotenv(sys.argv[1], override=True)
commands = [
    ("Creating missing tables", [sys.executable, "-m", "scripts.create_tables"]),
    ("Seeding missing permissions", [sys.executable, "-m", "scripts.seed_permissions"]),
    ("Seeding demo data", [sys.executable, "-m", "scripts.seed"] + (["--reset"] if sys.argv[2] == "true" else [])),
]
for message, command in commands:
    print(message + "...", flush=True)
    result = subprocess.run(command, env=os.environ.copy())
    if result.returncode:
        print("Error: " + message + " failed.", file=sys.stderr)
        sys.exit(result.returncode)
RUN_PY_END
echo "Database seed complete."
