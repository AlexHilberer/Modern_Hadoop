"""The original Phase 1 wordcount — classic Java MapReduce via Hadoop's
own bundled examples jar, run as a real MAPREDUCE-type YARN application."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="mapreduce_wordcount",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    BashOperator(
        task_id="java_mapreduce_wordcount",
        bash_command=(
            "hdfs dfs -rm -r -f /user/root/airflow-mapreduce-output && "
            "yarn jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar "
            "wordcount /user/root/input /user/root/airflow-mapreduce-output"
        ),
    )
