#!/bin/bash
set -e

mkdir -p "${AIRFLOW_HOME}"

until nc -z postgres 5432; do
  echo "Waiting for Postgres..."
  sleep 2
done

if [ ! -f "${AIRFLOW_HOME}/db-migrated" ]; then
  echo "Running Airflow DB migration..."
  airflow db migrate
  touch "${AIRFLOW_HOME}/db-migrated"
fi

exec airflow standalone
