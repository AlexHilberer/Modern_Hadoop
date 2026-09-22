# The official image bundles no DB drivers at all -- not even for its own
# Postgres metadata store. Needs both psycopg2 (Superset's own DB) and the
# same pyhive[hive] combo already proven against hiveserver2 elsewhere in
# this project (jupyterlab, Airflow). Installed via the image's own
# apt-install.sh/pip-install.sh helpers so they land in the actual venv the
# app runs from, not a stray system site-packages.
FROM apache/superset:6.1.0

USER root
RUN /app/docker/apt-install.sh libsasl2-dev libsasl2-modules python3-dev
RUN /app/docker/pip-install.sh --requires-build-essential \
      psycopg2-binary "pyhive[hive]" thrift sasl thrift-sasl

# /app/pythonpath is already on PYTHONPATH in the base image and is where
# Superset's own config loader looks for superset_config.py.
COPY superset_config.py /app/pythonpath/superset_config.py

# Checked-in dashboard/chart/dataset/database bundle (built once via the
# REST API -- see build_dashboard.py -- then exported and committed here)
# so the dashboard survives a fresh `docker compose up`, not just this
# container.
COPY --chown=superset:superset dashboards /app/dashboards

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER superset
ENTRYPOINT ["/entrypoint.sh"]
