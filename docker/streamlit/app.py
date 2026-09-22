"""Control panel for the Modern Hadoop stack: cluster health, stream
producer start/stop, per-engine job triggers, and terminal-style job output
-- all via the Airflow REST API, YARN's REST API, and the Docker socket.

Deliberately a plain Python container (not extending modern-hadoop-base) --
everything here happens over HTTP or the Docker socket, no Hadoop client
tooling needed."""
import time

import docker
import requests
import streamlit as st

from airflow_client import get_task_instances, list_recent_runs, read_task_output, trigger_dag
from config import AIRFLOW_URL, DAGS, STATE_LABEL, STREAM_PRODUCER_CONTAINER
from yarn_client import get_yarn_nodes

st.set_page_config(page_title="Modern Hadoop Control Panel", layout="wide")


@st.cache_resource
def docker_client():
    return docker.from_env()


st.title("Modern Hadoop Control Panel")

# --- Cluster health -----------------------------------------------------
st.header("Cluster health")
nodes = get_yarn_nodes()
if nodes is None:
    st.error("Could not reach YARN ResourceManager.")
else:
    cols = st.columns(4)
    healthy = sum(1 for n in nodes if n.get("state") == "RUNNING")
    cols[0].metric("YARN nodes", len(nodes))
    cols[1].metric("Healthy", healthy)
    total_mem = sum(n.get("availMemoryMB", 0) for n in nodes)
    cols[2].metric("Available memory", f"{total_mem} MB")
    cols[3].metric("Unhealthy", len(nodes) - healthy, delta_color="inverse")
    with st.expander("Node detail"):
        st.dataframe(
            [{"node": n["nodeHostName"], "state": n["state"], "containers": n.get("numContainers", 0)} for n in nodes],
            use_container_width=True,
        )

st.divider()

# --- Stream producer ------------------------------------------------------
st.header("Stream producer")
client = docker_client()
try:
    producer = client.containers.get(STREAM_PRODUCER_CONTAINER)
    running = producer.status == "running"
except docker.errors.NotFound:
    producer = None
    running = False

col1, col2, col3 = st.columns([1, 1, 3])
col1.write("Status:")
if running:
    col1.success("Running")
else:
    col1.warning("Stopped")
if col2.button("Start", disabled=running or producer is None):
    producer.start()
    st.rerun()
if col2.button("Stop", disabled=not running or producer is None):
    producer.stop()
    st.rerun()

st.divider()

# --- Job triggers -----------------------------------------------------
st.header("Run a job")
st.caption(
    "Each engine gets its own DAG; the full pipeline runs all five in "
    "sequence (the cluster is too small to usefully run them at once)."
)
cols = st.columns(len(DAGS))
for col, (dag_id, label) in zip(cols, DAGS):
    if col.button(label, key=f"trigger-{dag_id}"):
        try:
            run = trigger_dag(dag_id)
            st.session_state["selected_run"] = (dag_id, run["dag_run_id"])
            st.toast(f"Triggered {label}")
            time.sleep(1)
            st.rerun()
        except requests.RequestException as e:
            st.error(f"Failed to trigger {label}: {e}")

st.divider()

# --- Recent runs -----------------------------------------------------
st.header("Recent DAG runs")
try:
    runs = list_recent_runs()
except requests.RequestException as e:
    runs = []
    st.error(f"Could not reach Airflow: {e}")

if runs:
    st.dataframe(
        [
            {
                "DAG": r["dag_id"],
                "State": STATE_LABEL.get(r["state"], r["state"]),
                "Started": r.get("start_date", ""),
                "Ended": r.get("end_date", ""),
            }
            for r in runs
        ],
        use_container_width=True,
    )
else:
    st.info("No DAG runs yet, trigger one above.")

st.caption(f"Airflow UI: [{AIRFLOW_URL}]({AIRFLOW_URL})")

st.divider()

# --- Job output --------------------------------------------------------
st.header("Job output")

if runs:
    run_by_label = {
        f"{r['dag_id']} | {r.get('start_date', '')} | {STATE_LABEL.get(r['state'], r['state'])}": (
            r["dag_id"],
            r["dag_run_id"],
        )
        for r in runs
    }
    labels = list(run_by_label.keys())
    default_index = 0
    selected = st.session_state.get("selected_run")
    if selected in run_by_label.values():
        default_index = list(run_by_label.values()).index(selected)
    picked_label = st.selectbox("Run", labels, index=default_index)
    st.session_state["selected_run"] = run_by_label[picked_label]

    @st.fragment
    def show_job_output():
        dag_id, run_id = st.session_state["selected_run"]
        try:
            tasks = get_task_instances(dag_id, run_id)
        except requests.RequestException as e:
            st.error(f"Could not load task instances: {e}")
            return

        any_active = any(t["state"] in ("running", "queued", "scheduled") for t in tasks)
        for t in tasks:
            label = STATE_LABEL.get(t["state"], t["state"])
            duration = f"{t['duration']:.1f}s" if t.get("duration") else "n/a"
            st.caption(f"{label} **{t['task_id']}** | {t['state']} | {duration}")
            st.code(read_task_output(dag_id, run_id, t["task_id"]), language=None)

        if any_active:
            time.sleep(3)
            st.rerun(scope="fragment")

    show_job_output()
else:
    st.info("No DAG runs yet, trigger one above.")
