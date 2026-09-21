"""HBase read/write demo, standalone (see pipeline_dag.py for the full
multi-engine pipeline)."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="hbase_demo",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    BashOperator(
        task_id="hbase_put_get_scan",
        bash_command="hbase shell < /jobs/hbase/demo.hbase",
    )
