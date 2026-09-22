"""Classic MapReduce wordcount via mrjob's Hadoop runner, same input as the
Spark job, run through real Hadoop Streaming on the live YARN cluster.

Usage: python3 wordcount.py -r hadoop hdfs:///user/root/input/sample.txt \
           --hadoop-streaming-jar "$HADOOP_STREAMING_JAR" \
           -o hdfs:///user/root/mrjob-output
"""
from mrjob.job import MRJob


class MRWordCount(MRJob):
    def mapper(self, _, line):
        for word in line.split():
            yield word, 1

    def reducer(self, word, counts):
        yield word, sum(counts)


if __name__ == "__main__":
    MRWordCount.run()
