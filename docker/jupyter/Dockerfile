# Extends the shared Hadoop image so notebooks can talk to Spark-on-YARN,
# Hive, and HBase directly, without any remote execution machinery.
FROM modern-hadoop-base:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
      libsasl2-dev libsasl2-modules build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir jupyterlab "pyhive[hive]" happybase thrift sasl

# Spark's Python API isn't pip-installed separately (that would bundle a
# second, possibly-conflicting Spark distribution). Point Python at the
# already-installed $SPARK_HOME instead, the standard way to wire an
# existing Spark install into a plain Python process.
ENV PYTHONPATH=${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.7-src.zip

COPY spark-defaults.conf ${SPARK_HOME}/conf/spark-defaults.conf

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
