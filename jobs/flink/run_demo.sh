#!/bin/bash
# Flink jobs are unbounded streams, so a "run to completion" DAG task
# doesn't make sense the way it does for batch jobs. This submits
# detached, confirms it's genuinely RUNNING on YARN, lets it process the
# stream briefly, then tears it down, demonstrating real functionality
# without leaving a permanent resource hog on our tiny 4GB-total cluster.
set -e

export HADOOP_CLASSPATH=$(hadoop classpath)

echo "Submitting Flink job (detached)..."
# Flink's own JM+TM defaults (1600m + 1728m) each round up to the full
# 2048MB YARN allocation unit, needing 100% of our tiny 4GB-total
# cluster's capacity -- any other job running at the same time (even a
# small one) then blocks this in ACCEPTED forever. Shrinking both to fit
# exactly one allocation unit each leaves real headroom. Note: the legacy
# -yjm/-ytm flags are required here -- the generic -D
# jobmanager/taskmanager.memory.process.size overrides are silently
# ignored by `flink run -m yarn-cluster`.
OUTPUT=$(flink run -d -m yarn-cluster \
  -yjm 1024 \
  -ytm 1024 \
  -py /jobs/flink/stream_job.py 2>&1)
echo "$OUTPUT"

APP_ID=$(echo "$OUTPUT" | grep -oE 'application_[0-9]+_[0-9]+' | head -1)
if [ -z "$APP_ID" ]; then
  echo "Could not determine YARN application ID from Flink output" >&2
  exit 1
fi

echo "Flink job submitted as $APP_ID, waiting for RUNNING state..."
STATE=""
for i in $(seq 1 30); do
  STATE=$(yarn application -status "$APP_ID" 2>/dev/null | grep -E '^\s*State :' | awk -F': ' '{print $2}' | tr -d ' \t')
  echo "  state: $STATE"
  [ "$STATE" == "RUNNING" ] && break
  sleep 2
done

if [ "$STATE" != "RUNNING" ]; then
  echo "Flink job never reached RUNNING state (last seen: $STATE)" >&2
  yarn application -kill "$APP_ID" 2>/dev/null || true
  exit 1
fi

echo "Flink job is running, letting it process the stream for 20s..."
sleep 20

echo "Demo complete, tearing down the job..."
yarn application -kill "$APP_ID"
echo "Done."
