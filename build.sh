#!/usr/bin/env bash
# Render build script. Runs on every deploy.
# Configure this as the service's "Build Command": ./build.sh
set -o errexit  # exit on first error

pip install -r requirements.txt

# Collect static files for WhiteNoise to serve.
python manage.py collectstatic --no-input

# Apply database migrations.
python manage.py migrate

# Create role Groups + permissions (idempotent).
python manage.py setup_roles

# Create/update the super-administrator from DJANGO_SUPERUSER_* env vars
# (no-op if they aren't set). Render free tier has no Shell, so this is how
# the oversight superuser gets created on the live database.
python manage.py ensure_superuser

# Clear any brute-force lockouts on each deploy. Render's free tier has no
# Shell, so this is how a locked-out account gets unlocked: just redeploy.
python manage.py axes_reset

# Seed demo data (accounts, sensors, incidents, a warning) only when asked,
# so production deploys don't repeatedly reseed. Set SEED_DEMO=1 to enable.
if [ "${SEED_DEMO:-0}" = "1" ]; then
  python manage.py seed_demo
fi
