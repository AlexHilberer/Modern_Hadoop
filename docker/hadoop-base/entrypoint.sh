#!/bin/bash
set -e

mkdir -p "${HADOOP_HOME}/logs"
touch "${HADOOP_HOME}/logs/dummy.log"

wait_for_hdfs() {
  until hdfs dfs -test -d / 2>/dev/null; do
    echo "Waiting for HDFS..."
    sleep 2
  done
  echo "Waiting for NameNode to leave safe mode..."
  hdfs dfsadmin -safemode wait
}

wait_for_tcp() {
  until nc -z "$1" "$2"; do
    echo "Waiting for $1:$2..."
    sleep 2
  done
}

case "$NODE_ROLE" in
  master)
    if [ ! -f /opt/hadoop-data/nn/formatted ]; then
      echo "Formatting NameNode..."
      hdfs namenode -format -force -nonInteractive
      touch /opt/hadoop-data/nn/formatted
    fi
    hdfs --daemon start namenode
    yarn --daemon start resourcemanager

    wait_for_hdfs
    hdfs dfs -mkdir -p /hbase

    if [ ! -f /opt/hadoop-data/tez-uploaded ]; then
      echo "Uploading Tez runtime to HDFS..."
      tar -czf /tmp/tez.tar.gz -C "${TEZ_HOME}" .
      hdfs dfs -mkdir -p /apps/tez
      hdfs dfs -put -f /tmp/tez.tar.gz /apps/tez/tez.tar.gz
      rm /tmp/tez.tar.gz
      touch /opt/hadoop-data/tez-uploaded
    fi

    if [ ! -f /opt/hadoop-data/spark-jars-uploaded ]; then
      echo "Uploading Spark jars to HDFS..."
      hdfs dfs -mkdir -p /apps/spark/jars
      hdfs dfs -put -f "${SPARK_HOME}"/jars/*.jar /apps/spark/jars/
      touch /opt/hadoop-data/spark-jars-uploaded
    fi

    ;;
  hive-metastore)
    wait_for_tcp hadoop-master 9000
    wait_for_hdfs
    hdfs dfs -mkdir -p /user/hive/warehouse
    hdfs dfs -chmod -R 1777 /user/hive/warehouse

    wait_for_tcp postgres 5432

    # Idempotent by checking the schema itself (not a marker file) — this
    # container's own volume has no memory of prior runs on a different
    # container, but the schema's actual presence in Postgres does.
    if ! schematool -dbType postgres -info > /dev/null 2>&1; then
      echo "Initializing Hive metastore schema..."
      schematool -dbType postgres -initSchema
    fi

    exec hive --service metastore
    ;;
  hiveserver2)
    wait_for_tcp hive-metastore 9083
    exec hive --service hiveserver2
    ;;
  worker)
    wait_for_tcp hadoop-master 9000
    hdfs --daemon start datanode
    yarn --daemon start nodemanager

    wait_for_tcp zookeeper 2181
    hbase-daemon.sh start regionserver
    ;;
  zookeeper)
    hbase-daemon.sh start zookeeper
    ;;
  hbase-master)
    wait_for_tcp hadoop-master 9000
    wait_for_tcp zookeeper 2181
    hbase-daemon.sh start master
    hbase-daemon.sh start thrift
    ;;
  *)
    echo "NODE_ROLE must be one of: master, worker, zookeeper, hbase-master, hive-metastore, hiveserver2" >&2
    exit 1
    ;;
esac

exec tail -F "${HADOOP_HOME}"/logs/*.log
