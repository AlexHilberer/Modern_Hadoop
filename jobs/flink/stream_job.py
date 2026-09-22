"""Continuously reads the number files stream-producer writes to HDFS and
doubles each value, submitted to YARN as a real Flink job.

PyFlink's Python DataStream API has no built-in raw-socket source, so this
uses Flink's FileSource in continuous-monitoring mode against the HDFS
directory stream-producer writes into, a real distributed source that
works regardless of which YARN node the TaskManager lands on.

Usage: export HADOOP_CLASSPATH=$(hadoop classpath) && \
           flink run -m yarn-cluster -py stream_job.py

HADOOP_CLASSPATH is scoped to this command deliberately, not set globally,
see the note above HADOOP_CLASSPATH in docker/hadoop-base/Dockerfile.
"""
from pyflink.common import Duration, WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.file_system import FileSource, StreamFormat

STREAM_DIR = "hdfs://hadoop-master:9000/stream/numbers"


def main():
    env = StreamExecutionEnvironment.get_execution_environment()

    source = (
        FileSource.for_record_stream_format(StreamFormat.text_line_format(), STREAM_DIR)
        .monitor_continuously(Duration.of_seconds(1))
        .build()
    )
    stream = env.from_source(source, WatermarkStrategy.no_watermarks(), "numbers")

    doubled = stream.map(lambda line: int(line.strip()) * 2)
    doubled.print()

    env.execute("stream-producer doubler")


if __name__ == "__main__":
    main()
