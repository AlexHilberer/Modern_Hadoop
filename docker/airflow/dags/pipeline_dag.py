"""Chains the Phase 3 jobs into one pipeline: Spark wordcount, then mrjob
wordcount (same input, for comparison), then the Hive-on-Tez sample query.
Sequential on purpose — the 2-worker/2GB-per-node YARN cluster is too small
to usefully run these concurrently."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="modern_hadoop_pipeline",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    spark_wordcount = BashOperator(
        task_id="spark_wordcount",
        bash_command=(
            "hdfs dfs -rm -r -f /user/root/airflow-spark-output && "
            "spark-submit --master yarn --deploy-mode cluster "
            "/jobs/spark/example_job.py "
            "hdfs:///user/root/input hdfs:///user/root/airflow-spark-output"
        ),
    )

    mrjob_wordcount = BashOperator(
        task_id="mrjob_wordcount",
        bash_command=(
            "hdfs dfs -rm -r -f /user/root/airflow-mrjob-output && "
            "python3 /jobs/mrjob/wordcount.py -r hadoop "
            "hdfs:///user/root/input/sample.txt "
            '--hadoop-streaming-jar "$HADOOP_STREAMING_JAR" '
            "-o hdfs:///user/root/airflow-mrjob-output"
        ),
    )

    hive_query = BashOperator(
        task_id="hive_query",
        # `-f <file>` hits a beeline code path that still tries to build a
        # terminal even non-interactively and fails; stdin redirection uses
        # the same script-mode path as `-e` and actually works headless.
        bash_command=(
            "beeline -u jdbc:hive2://hadoop-master:10000 -n root "
            "< /jobs/hive/sample_queries.sql"
        ),
    )

    spark_wordcount >> mrjob_wordcount >> hive_query
