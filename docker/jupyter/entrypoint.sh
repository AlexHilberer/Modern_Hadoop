#!/bin/bash
set -e

exec jupyter lab \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --notebook-dir=/opt/notebooks \
  --ServerApp.token='' \
  --ServerApp.password=''
