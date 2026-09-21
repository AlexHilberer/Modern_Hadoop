"""Writes an incrementing counter to HDFS once a second, one small file per
number, via WebHDFS — the data source Flink's stream job continuously reads
from."""
import time

from hdfs import InsecureClient

NAMENODE_WEBHDFS_URL = "http://hadoop-master:9870"
STREAM_DIR = "/stream/numbers"


def main():
    client = InsecureClient(NAMENODE_WEBHDFS_URL, user="root")
    client.makedirs(STREAM_DIR)

    n = 0
    while True:
        path = f"{STREAM_DIR}/{n:012d}.txt"
        client.write(path, data=f"{n}\n", overwrite=True)
        print(f"wrote {path}", flush=True)
        n += 1
        time.sleep(1)


if __name__ == "__main__":
    main()
