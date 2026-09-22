"""The flagship demo: the same wordcount data run through every engine in
the stack, then Hive-on-Tez, HBase, and a brief Flink streaming run, all in
one DAG. Sequential on purpose, since the 2-worker/2GB-per-node YARN
cluster is too small to usefully run these concurrently (we've seen
firsthand how easily a single lingering job can starve everything else on
a cluster this size)."""
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
            "hdfs dfs -mkdir -p /user/root/input && "
            "hdfs dfs -put -f /jobs/wordcount/sample.txt /user/root/input/sample.txt && "
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
            "hdfs dfs -mkdir -p /data/people && "
            "hdfs dfs -put -f /jobs/hive/people.csv /data/people/people.csv && "
            "beeline -u jdbc:hive2://hiveserver2:10000 -n root "
            "< /jobs/hive/sample_queries.sql"
        ),
    )

    hbase_demo = BashOperator(
        task_id="hbase_put_get_scan",
        bash_command="hbase shell < /jobs/hbase/demo.hbase",
    )

    flink_demo = BashOperator(
        task_id="flink_stream_demo",
        # Trailing space is deliberate: BashOperator treats a bash_command
        # ending in .sh as a Jinja template *file* to load from the DAGs
        # folder rather than literal shell text, and fails instantly.
        bash_command="bash /jobs/flink/run_demo.sh ",
    )

    spark_wordcount >> mrjob_wordcount >> hive_query >> hbase_demo >> flink_demo
