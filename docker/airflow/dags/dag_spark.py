"""Spark wordcount on YARN, standalone (see pipeline_dag.py for the full
multi-engine pipeline)."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="spark_wordcount",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    BashOperator(
        task_id="spark_wordcount",
        bash_command=(
            "hdfs dfs -mkdir -p /user/root/input && "
            "hdfs dfs -put -f /jobs/wordcount/sample.txt /user/root/input/sample.txt && "
            "hdfs dfs -rm -r -f /user/root/airflow-spark-output && "
            "spark-submit --master yarn --deploy-mode cluster "
            "/jobs/spark/example_job.py "
            "hdfs:///user/root/input hdfs:///user/root/airflow-spark-output"
        ),
    )
