"""Airflow REST API client: auth, DAG triggering, and terminal-style task
output reconstructed from the structlog task logs on the shared, read-only
`airflow-data` volume."""
import glob
import json

import requests
import streamlit as st

from config import AIRFLOW_LOGS_DIR, AIRFLOW_PASSWORD_FILE, AIRFLOW_URL


@st.cache_data(ttl=60)
def get_airflow_token():
    with open(AIRFLOW_PASSWORD_FILE) as f:
        password = json.load(f)["admin"]
    resp = requests.post(
        f"{AIRFLOW_URL}/auth/token",
        json={"username": "admin", "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers():
    return {"Authorization": f"Bearer {get_airflow_token()}"}


def trigger_dag(dag_id):
    resp = requests.post(
        f"{AIRFLOW_URL}/api/v2/dags/{dag_id}/dagRuns",
        headers=_headers(),
        json={"logical_date": None},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def list_recent_runs(limit=20):
    resp = requests.post(
        f"{AIRFLOW_URL}/api/v2/dags/~/dagRuns/list",
        headers=_headers(),
        json={"order_by": "-start_date", "page_limit": limit},
        timeout=10,
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("dag_runs", [])


def get_task_instances(dag_id, run_id):
    resp = requests.get(
        f"{AIRFLOW_URL}/api/v2/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return sorted(resp.json()["task_instances"], key=lambda t: t.get("start_date") or "")


def read_task_output(dag_id, run_id, task_id, max_lines=400):
    """Reconstruct terminal-style output from a task's structlog JSON log.

    Each BashOperator stdout/stderr line is logged by SubprocessHook with the
    real text in "event"; error-level lines from elsewhere (e.g. a DAG
    failing before the subprocess ever ran) are surfaced too so failures are
    diagnosable from here, not just successes."""
    pattern = f"{AIRFLOW_LOGS_DIR}/dag_id={dag_id}/run_id={run_id}/task_id={task_id}/attempt=*.log"
    attempts = sorted(glob.glob(pattern))
    if not attempts:
        return "(waiting for logs...)"

    lines = []
    with open(attempts[-1]) as f:
        for raw_line in f:
            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            event = entry.get("event", "")
            if "SubprocessHook" in entry.get("logger", ""):
                lines.append(event)
            elif entry.get("level") == "error" and event:
                lines.append(f"ERROR: {event}")
    if not lines:
        return "(no output yet)"
    return "\n".join(lines[-max_lines:])
