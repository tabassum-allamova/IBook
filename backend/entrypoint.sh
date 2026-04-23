#!/bin/sh
set -e

# -----------------------------------------------------------------------------
# Wait for the database to accept connections before running migrations.
# -----------------------------------------------------------------------------
if [ -n "$DATABASE_URL" ]; then
  echo "[entrypoint] Waiting for database..."
  python - <<'PY'
import os, socket, time
from urllib.parse import urlparse

url = urlparse(os.environ["DATABASE_URL"])
host = url.hostname or "localhost"
port = url.port or 5432

deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[entrypoint] Database {host}:{port} is accepting connections.")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f"[entrypoint] Timed out waiting for {host}:{port}")
PY
fi

# -----------------------------------------------------------------------------
# Apply migrations.
# -----------------------------------------------------------------------------
echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

# -----------------------------------------------------------------------------
# First-run demo seed. We only seed an empty database — once there are any
# users the command is skipped so restarts don't duplicate data or block on
# the external photo downloads inside seed_demo.
# -----------------------------------------------------------------------------
if [ "${SKIP_SEED:-0}" != "1" ]; then
  HAS_USERS=$(python manage.py shell -c "from django.contrib.auth import get_user_model; import sys; sys.stdout.write('1' if get_user_model().objects.exists() else '0')" 2>/dev/null || echo "0")
  if [ "$HAS_USERS" = "0" ]; then
    echo "[entrypoint] Empty database — seeding demo data..."
    python manage.py seed_demo || echo "[entrypoint] Seed failed (continuing); run 'python manage.py seed_demo' manually to retry."
  else
    echo "[entrypoint] Database already seeded — skipping."
  fi
fi

# -----------------------------------------------------------------------------
# Hand off to the container CMD (runserver / gunicorn / tests / …).
# -----------------------------------------------------------------------------
exec "$@"
