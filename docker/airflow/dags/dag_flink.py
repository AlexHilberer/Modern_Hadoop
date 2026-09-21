"""Flink streaming demo, standalone (see pipeline_dag.py for the full
multi-engine pipeline). See jobs/flink/run_demo.sh for why this submits,
confirms it's running, then tears itself down rather than running forever."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="flink_stream_demo",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    BashOperator(
        task_id="flink_stream_demo",
        # Trailing space is deliberate: BashOperator treats a bash_command
        # ending in .sh as a Jinja template *file* to load from the DAGs
        # folder rather than literal shell text, and fails instantly.
        bash_command="bash /jobs/flink/run_demo.sh ",
    )
