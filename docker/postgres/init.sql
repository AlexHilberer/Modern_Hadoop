-- One shared Postgres instance backs Hive Metastore, Airflow, and Superset,
-- each in its own database/user so they never see each other's tables.
CREATE USER hive WITH PASSWORD 'hive';
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE USER superset WITH PASSWORD 'superset';

CREATE DATABASE hive_metastore OWNER hive;
CREATE DATABASE airflow OWNER airflow;
CREATE DATABASE superset OWNER superset;
