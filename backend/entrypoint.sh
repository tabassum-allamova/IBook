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
  # Decide whether to run the seed. It's idempotent (uses get_or_create
  # everywhere), so we re-run it whenever an expected slice is missing —
  # e.g. after adding solo barbers or after wiping shop photos that came
  # from a now-broken placeholder service. Force a full run with FORCE_SEED=1.
  #
  # Exit codes:
  #   1 = empty DB                    → first-run seed
  #   2 = needs top-up (missing data) → re-run idempotently
  #   0 = fully seeded                → skip
  # `set -e` would abort on a non-zero exit from this probe, so disable it
  # while we capture the status code.
  set +e
  python -c "
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
from apps.shops.models import ShopPhoto

User = get_user_model()
if not User.objects.exists():
    sys.exit(1)
needs_topup = (
    not ShopPhoto.objects.exists()
    or not User.objects.filter(role='BARBER', shop_memberships__isnull=True).exists()
)
sys.exit(2 if needs_topup else 0)
" 2>/dev/null
  seed_status=$?
  set -e

  if [ "${FORCE_SEED:-0}" = "1" ] || [ "$seed_status" -eq 1 ]; then
    echo "[entrypoint] Empty database — seeding demo data..."
    python manage.py seed_demo || echo "[entrypoint] Seed failed (continuing); run 'python manage.py seed_demo' manually to retry."
  elif [ "$seed_status" -eq 2 ]; then
    echo "[entrypoint] Existing data missing photos or solo barbers — topping up..."
    python manage.py seed_demo || echo "[entrypoint] Seed top-up failed (continuing); run 'python manage.py seed_demo' manually to retry."
  else
    echo "[entrypoint] Database already seeded — skipping."
  fi
fi

# -----------------------------------------------------------------------------
# Hand off to the container CMD (runserver / gunicorn / tests / …).
# -----------------------------------------------------------------------------
exec "$@"
