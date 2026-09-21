# Extends the shared Hadoop image so this container is itself a YARN edge
# node — its DAG tasks call spark-submit/mrjob/beeline directly, no remote
# execution needed.
FROM modern-hadoop-base:latest

ENV AIRFLOW_VERSION=3.3.2
ENV AIRFLOW_HOME=/opt/airflow-data
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
ENV AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
# Airflow 2.x is EOL (no more security patches); 3.x is the only real
# option now. The documented install method pins against a constraints
# file matching this exact Airflow + Python version, avoiding dependency
# resolution surprises.
RUN pip3 install --no-cache-dir "apache-airflow[postgres]==${AIRFLOW_VERSION}" \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.10.txt"

# beeline's jline terminal builder fails without a tty (see hadoop-base
# entrypoint history) — safe to bake in globally here since, unlike
# hadoop-base, this container runs no long-lived daemons whose logs it'd
# spam with "Picked up JAVA_TOOL_OPTIONS".
ENV JAVA_TOOL_OPTIONS="-Dorg.jline.terminal.provider=dumb -Dorg.jline.terminal.dumb=true"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
