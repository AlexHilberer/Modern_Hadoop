-- Hive 4 has no execution engine besides Tez, so any non-trivial query here
-- runs as a real Tez DAG on YARN.
SET hive.execution.engine=tez;

-- EXTERNAL + dropped/recreated every run: EXTERNAL means DROP TABLE only
-- removes the metadata, not the CSV the DAG just re-put at this location
-- (a managed table's DROP would delete the underlying data too). Keeps the
-- table schema in sync with jobs/hive/people.csv instead of drifting.
DROP TABLE IF EXISTS people;
CREATE EXTERNAL TABLE people (
  name STRING,
  age INT,
  department STRING,
  city STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/data/people'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT * FROM people;

SELECT COUNT(*) AS total_people, AVG(age) AS average_age FROM people;

SELECT department, COUNT(*) AS people_count, AVG(age) AS average_age
FROM people
GROUP BY department;

SELECT city, COUNT(*) AS people_count
FROM people
GROUP BY city;
