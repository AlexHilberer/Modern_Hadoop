"""Spark wordcount on YARN, same input as the mrjob wordcount, so the two
engines can be compared on identical data.

Usage: spark-submit --master yarn --deploy-mode cluster example_job.py \
           hdfs:///user/root/input hdfs:///user/root/spark-output
"""
import sys

from pyspark.sql import SparkSession


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "/user/root/input"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "/user/root/spark-output"

    spark = SparkSession.builder.appName("wordcount").getOrCreate()
    sc = spark.sparkContext

    counts = (
        sc.textFile(input_path)
        .flatMap(lambda line: line.split())
        .map(lambda word: (word, 1))
        .reduceByKey(lambda a, b: a + b)
    )
    counts.saveAsTextFile(output_path)

    spark.stop()


if __name__ == "__main__":
    main()
