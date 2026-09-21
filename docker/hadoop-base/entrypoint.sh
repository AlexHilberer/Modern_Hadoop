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
    hdfs dfs -mkdir -p /user/hive/warehouse
    hdfs dfs -mkdir -p /hbase
    hdfs dfs -chmod -R 1777 /user/hive/warehouse

    if [ ! -f /opt/hadoop-data/tez-uploaded ]; then
      echo "Uploading Tez runtime to HDFS..."
      tar -czf /tmp/tez.tar.gz -C "${TEZ_HOME}" .
      hdfs dfs -mkdir -p /apps/tez
      hdfs dfs -put -f /tmp/tez.tar.gz /apps/tez/tez.tar.gz
      rm /tmp/tez.tar.gz
      touch /opt/hadoop-data/tez-uploaded
    fi

    wait_for_tcp postgres 5432

    if [ ! -f /opt/hadoop-data/hive-schema-initialized ]; then
      echo "Initializing Hive metastore schema..."
      schematool -dbType postgres -initSchema
      touch /opt/hadoop-data/hive-schema-initialized
    fi

    hive --service metastore &
    sleep 10
    hive --service hiveserver2 &
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
    ;;
  *)
    echo "NODE_ROLE must be one of: master, worker, zookeeper, hbase-master" >&2
    exit 1
    ;;
esac

exec tail -F "${HADOOP_HOME}"/logs/*.log
