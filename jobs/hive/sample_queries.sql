-- Hive 4 has no execution engine besides Tez, so any non-trivial query here
-- runs as a real Tez DAG on YARN.
SET hive.execution.engine=tez;

CREATE TABLE IF NOT EXISTS people (
  name STRING,
  age INT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/data/people'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT * FROM people;

SELECT COUNT(*) AS total_people, AVG(age) AS average_age FROM people;
