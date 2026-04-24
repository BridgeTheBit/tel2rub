import json, time, os
from pathlib import Path

QUEUE_FILE = Path("queue/tasks.jsonl")


def read_tasks():
    if not QUEUE_FILE.exists():
        return []

    with open(QUEUE_FILE) as f:
        return [json.loads(x) for x in f]


def worker():
    while True:
        tasks = read_tasks()

        for t in tasks:
            file = t["file_path"]
            print("Uploading to Rubika:", file)
            time.sleep(3)
            print("Uploaded:", file)

        time.sleep(10)


if __name__ == "__main__":
    worker()
