"""Hive-on-Tez, standalone (see pipeline_dag.py for the full multi-engine
pipeline)."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="hive_tez_query",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    BashOperator(
        task_id="hive_query",
        # `-f <file>` hits a beeline code path that still tries to build a
        # terminal even non-interactively and fails; stdin redirection uses
        # the same script-mode path as `-e` and actually works headless.
        bash_command=(
            "hdfs dfs -mkdir -p /data/people && "
            "hdfs dfs -put -f /jobs/hive/people.csv /data/people/people.csv && "
            "beeline -u jdbc:hive2://hiveserver2:10000 -n root "
            "< /jobs/hive/sample_queries.sql"
        ),
    )
