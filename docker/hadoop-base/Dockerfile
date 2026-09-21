# Download stages: each is cached independently, keyed only by its own
# version ARG, so churn in the final stage (apt packages, configs,
# entrypoint) never forces a re-download. Stages beyond downloader-hadoop
# are pre-fetches for later phases — not wired into the final image yet.
# dlcdn.apache.org is the fast current-release mirror network; it only
# keeps recent releases, so pin versions that are actually present there.
FROM ubuntu:22.04 AS downloader-base
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

FROM downloader-base AS downloader-hadoop
ARG HADOOP_VERSION=3.4.3
RUN curl -fsSL https://dlcdn.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
      -o /tmp/hadoop.tar.gz

FROM downloader-base AS downloader-hive
ARG HIVE_VERSION=4.2.1
RUN curl -fsSL https://dlcdn.apache.org/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz \
      -o /tmp/hive.tar.gz

FROM downloader-base AS downloader-tez
ARG TEZ_VERSION=0.10.5
RUN curl -fsSL https://dlcdn.apache.org/tez/${TEZ_VERSION}/apache-tez-${TEZ_VERSION}-bin.tar.gz \
      -o /tmp/tez.tar.gz

# HBase 2.x's "-bin" release bundles an old Hadoop 2.10.2 client and its
# compiled bytecode expects Hadoop 2's nested DFSInputStream$ReadStatistics
# return type from HdfsDataInputStream.getReadStatistics() — every current
# Hadoop 3.x release already refactored that to a top-level class, so 2.x
# fails with NoSuchMethodError at HMaster startup against ANY real Hadoop
# 3.x, not just newer ones. HBase 3.0.0 bundles Hadoop 3.4.3 itself, so it's
# actually compiled against the modern API shape.
FROM downloader-base AS downloader-hbase
ARG HBASE_VERSION=3.0.0
RUN curl -fsSL https://dlcdn.apache.org/hbase/${HBASE_VERSION}/hbase-${HBASE_VERSION}-bin.tar.gz \
      -o /tmp/hbase.tar.gz

FROM downloader-base AS downloader-spark
ARG SPARK_VERSION=3.5.9
RUN curl -fsSL https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz \
      -o /tmp/spark.tgz

# Flink-on-YARN needs the real Hadoop classpath (not just Tez's, unlike
# Hive/HBase which launch via `hadoop jar`/RunJar and get it automatically)
# exported as HADOOP_CLASSPATH — see the final stage below.
FROM downloader-base AS downloader-flink
ARG FLINK_VERSION=1.20.5
RUN curl -fsSL https://dlcdn.apache.org/flink/flink-${FLINK_VERSION}/flink-${FLINK_VERSION}-bin-scala_2.12.tgz \
      -o /tmp/flink.tgz

FROM downloader-base AS downloader-postgres-jdbc
ARG POSTGRES_JDBC_VERSION=42.7.4
RUN curl -fsSL https://repo1.maven.org/maven2/org/postgresql/postgresql/${POSTGRES_JDBC_VERSION}/postgresql-${POSTGRES_JDBC_VERSION}.jar \
      -o /tmp/postgresql.jar

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HADOOP_VERSION=3.4.3
ENV HIVE_VERSION=4.2.1
ENV HBASE_VERSION=3.0.0
ENV TEZ_VERSION=0.10.5
ENV SPARK_VERSION=3.5.9
ENV FLINK_VERSION=1.20.5
ENV HADOOP_HOME=/opt/hadoop
ENV HIVE_HOME=/opt/hive
ENV HBASE_HOME=/opt/hbase
ENV TEZ_HOME=/opt/tez
ENV SPARK_HOME=/opt/spark
ENV FLINK_HOME=/opt/flink
ENV TEZ_CONF_DIR=${TEZ_HOME}/conf
ENV HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
# Hive 4 has no MapReduce engine anymore — HiveServer2 needs Tez classes on
# its own classpath just to start, regardless of query complexity.
#
# NOT including Hadoop's own share/hadoop/*/lib globs here: they were here
# briefly for Flink-on-YARN (which needs the real Hadoop classpath exported
# as HADOOP_CLASSPATH, per Flink's own docs), but that leaked Hadoop's
# bundled old jline-3.9.0.jar (share/hadoop/yarn/lib/) onto every
# Hadoop-launched process's classpath — including beeline, which conflicts
# with Hive's own modern jline-3.25.0.jar and breaks terminal building
# entirely. Same class of bug as the Tez/HBase bundled-jar conflicts.
# Flink needs `export HADOOP_CLASSPATH=$(hadoop classpath)` scoped to its
# own invocation instead — see jobs/flink/stream_job.py's usage comment.
ENV HADOOP_CLASSPATH=${TEZ_CONF_DIR}:${TEZ_HOME}/*:${TEZ_HOME}/lib/*
ENV HADOOP_STREAMING_JAR=${HADOOP_HOME}/share/hadoop/tools/lib/hadoop-streaming-${HADOOP_VERSION}.jar
# One JDK cluster-wide. Hive 4.2.x's classes (compiled for Java 21) end up
# loaded not just in HiveServer2 but inside Tez AM/task containers on the
# worker nodes too, so every JVM in the cluster needs to be Java 21 — a
# split JDK setup (17 elsewhere) doesn't work for Hive-on-Tez.
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${HIVE_HOME}/bin:${HBASE_HOME}/bin:${SPARK_HOME}/bin:${FLINK_HOME}/bin:${JAVA_HOME}/bin:${PATH}
# Hadoop 3.3.x's launch scripts don't auto-inject the --add-opens flags
# newer JDKs need for reflection (3.4.x's scripts do) — without these,
# ResourceManager's Guice/cglib-based webapp fails with
# InaccessibleObjectException on startup under Java 17+/21.
ENV HADOOP_OPTS="--add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.math=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.text=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.util.concurrent=ALL-UNNAMED --add-opens=java.base/java.util.zip=ALL-UNNAMED --add-opens=java.base/sun.security.util=ALL-UNNAMED --add-opens=java.base/sun.security.x509=ALL-UNNAMED"
ENV HDFS_NAMENODE_USER=root
ENV HDFS_DATANODE_USER=root
ENV HDFS_SECONDARYNAMENODE_USER=root
ENV YARN_RESOURCEMANAGER_USER=root
ENV YARN_NODEMANAGER_USER=root

RUN apt-get update && apt-get install -y --no-install-recommends \
      openjdk-21-jdk-headless ca-certificates netcat-openbsd procps \
      python3 python3-pip python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# apache-flink's version must match FLINK_VERSION exactly — it's the Python
# API binding for the same Flink distribution, not an independent library.
RUN pip3 install --no-cache-dir mrjob apache-flink==${FLINK_VERSION}

COPY --from=downloader-hadoop /tmp/hadoop.tar.gz /tmp/hadoop.tar.gz
RUN tar -xzf /tmp/hadoop.tar.gz -C /opt \
    && mv /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} \
    && rm /tmp/hadoop.tar.gz

RUN echo "export JAVA_HOME=${JAVA_HOME}" >> ${HADOOP_HOME}/etc/hadoop/hadoop-env.sh

COPY --from=downloader-hive /tmp/hive.tar.gz /tmp/hive.tar.gz
RUN tar -xzf /tmp/hive.tar.gz -C /opt \
    && mv /opt/apache-hive-${HIVE_VERSION}-bin ${HIVE_HOME} \
    && rm /tmp/hive.tar.gz

COPY --from=downloader-hbase /tmp/hbase.tar.gz /tmp/hbase.tar.gz
RUN tar -xzf /tmp/hbase.tar.gz -C /opt \
    && mv /opt/hbase-${HBASE_VERSION} ${HBASE_HOME} \
    && rm /tmp/hbase.tar.gz

COPY --from=downloader-tez /tmp/tez.tar.gz /tmp/tez.tar.gz
# Tez bundles its own (different-version) hadoop-hdfs-client in lib/. Since
# HADOOP_CLASSPATH below exposes TEZ_HOME/lib to every Hadoop-launched
# process (not just Tez's own YARN containers), that jar leaks onto
# HiveServer2's classpath and clashes with our actual Hadoop HDFS client
# (same fix as HBase's bundled jars). Only removing hadoop-hdfs-client:
# tez.use.cluster.hadoop-libs=true supplies the real common/hdfs/yarn libs
# to Tez's own YARN containers, but NOT the separate MapReduce framework
# libs — Tez's own mapreduce-compat shim needs its bundled
# hadoop-mapreduce-client-core/-common (org.apache.hadoop.mapred.JobConf
# etc.) to stay, or the AM fails with NoClassDefFoundError.
RUN tar -xzf /tmp/tez.tar.gz -C /opt \
    && mv /opt/apache-tez-${TEZ_VERSION}-bin ${TEZ_HOME} \
    && rm /tmp/tez.tar.gz \
    && mkdir -p ${TEZ_CONF_DIR} \
    && cp ${HIVE_HOME}/lib/commons-collections-3.2.2.jar ${TEZ_HOME}/lib/ \
    && rm -f ${TEZ_HOME}/lib/hadoop-hdfs-client-*.jar

COPY --from=downloader-spark /tmp/spark.tgz /tmp/spark.tgz
RUN tar -xzf /tmp/spark.tgz -C /opt \
    && mv /opt/spark-${SPARK_VERSION}-bin-hadoop3 ${SPARK_HOME} \
    && rm /tmp/spark.tgz

COPY --from=downloader-flink /tmp/flink.tgz /tmp/flink.tgz
RUN tar -xzf /tmp/flink.tgz -C /opt \
    && mv /opt/flink-${FLINK_VERSION} ${FLINK_HOME} \
    && rm /tmp/flink.tgz

COPY --from=downloader-postgres-jdbc /tmp/postgresql.jar ${HIVE_HOME}/lib/postgresql.jar

COPY conf/core-site.xml conf/hdfs-site.xml conf/yarn-site.xml conf/mapred-site.xml ${HADOOP_HOME}/etc/hadoop/
COPY conf/workers ${HADOOP_HOME}/etc/hadoop/workers
COPY conf/hive-site.xml ${HIVE_HOME}/conf/hive-site.xml
COPY conf/hbase-site.xml ${HBASE_HOME}/conf/hbase-site.xml
COPY conf/tez-site.xml ${TEZ_CONF_DIR}/tez-site.xml
COPY conf/spark-defaults.conf ${SPARK_HOME}/conf/spark-defaults.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /opt/hadoop-data/nn /opt/hadoop-data/dn /opt/hadoop-data/zk

ENTRYPOINT ["/entrypoint.sh"]
