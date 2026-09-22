#!/bin/bash
set -e

# Reuses the official image's own init sequence (db migrate, admin user,
# roles/permissions) -- it's idempotent, safe to run on every container
# start, and stays correct across Superset upgrades instead of us
# reimplementing it.
/app/docker/docker-init.sh

# Re-import the checked-in dashboard bundle every start so it survives a
# fresh `docker compose up` (--overwrite makes this idempotent -- matches
# by UUID instead of duplicating).
superset import-directory /app/dashboards --overwrite

exec /app/docker/entrypoints/run-server.sh
