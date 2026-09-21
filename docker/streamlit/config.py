"""Shared constants for the control panel."""

AIRFLOW_URL = "http://airflow:8080"
AIRFLOW_PASSWORD_FILE = "/opt/airflow-data/simple_auth_manager_passwords.json.generated"
AIRFLOW_LOGS_DIR = "/opt/airflow-data/logs"
YARN_RM_URL = "http://hadoop-master:8088"
STREAM_PRODUCER_CONTAINER = "stream-producer"

DAGS = [
    ("modern_hadoop_pipeline", "Full pipeline (all 5 engines)"),
    ("mapreduce_wordcount", "MapReduce (Java)"),
    ("spark_wordcount", "Spark"),
    ("hive_tez_query", "Hive on Tez"),
    ("hbase_demo", "HBase"),
    ("flink_stream_demo", "Flink"),
]

STATE_EMOJI = {"success": "✅", "failed": "❌", "running": "🔄", "queued": "⏳"}
