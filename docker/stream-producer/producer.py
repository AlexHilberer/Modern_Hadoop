"""Writes an incrementing counter to HDFS once a second, one small file per
number, via WebHDFS. This is the data source Flink's stream job
continuously reads from."""
import time

from hdfs import InsecureClient
from requests.exceptions import ConnectionError as RequestsConnectionError

NAMENODE_WEBHDFS_URL = "http://hadoop-master:9870"
STREAM_DIR = "/stream/numbers"


def main():
    client = InsecureClient(NAMENODE_WEBHDFS_URL, user="root")
    while True:
        try:
            client.makedirs(STREAM_DIR)
            break
        except RequestsConnectionError:
            print("Waiting for HDFS...", flush=True)
            time.sleep(2)

    n = 0
    while True:
        path = f"{STREAM_DIR}/{n:012d}.txt"
        client.write(path, data=f"{n}\n", overwrite=True)
        print(f"wrote {path}", flush=True)
        n += 1
        time.sleep(1)


if __name__ == "__main__":
    main()
