import os
import json
import time
import shutil
import logging
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from rubpy import RubikaClient
from rubpy.exceptions import *

# =========================
# Load ENV
# =========================

load_dotenv()

RUBIKA_SESSION = os.getenv("RUBIKA_SESSION")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")

QUEUE_FILE = "tasks.jsonl"
FAILED_FILE = "failed.jsonl"
PROCESSING_FILE = "processing.json"

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
BASE_RETRY_DELAY = int(os.getenv("RETRY_DELAY", 3))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 2))

KEEP_EXTENSIONS = {".mp4", ".mp3", ".pdf", ".jpg", ".png", ".zip"}

# =========================
# Logging (JSON structured)
# =========================

logging.basicConfig(
    filename="worker.log",
    level=logging.INFO,
    format="%(message)s"
)

def log(level, message, **kwargs):
    entry = {
        "level": level,
        "message": message,
        "timestamp": time.time(),
        **kwargs
    }
    logging.info(json.dumps(entry, ensure_ascii=False))


# =========================
# Helpers
# =========================

def is_retryable_error(e: Exception) -> bool:
    retry_keywords = [
        "timeout",
        "gateway",
        "temporarily",
        "chunk",
        "connection",
        "rate"
    ]
    return any(k in str(e).lower() for k in retry_keywords)


def send_with_retry(client, file_path, caption):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client.send_document(
                TARGET_CHANNEL,
                file_path,
                caption=caption
            )
            log("INFO", "file_sent", file=file_path)
            return True

        except Exception as e:
            retryable = is_retryable_error(e)

            log("ERROR", "send_failed",
                file=file_path,
                attempt=attempt,
                error=str(e),
                retryable=retryable)

            if not retryable:
                raise e

            delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
            time.sleep(delay)

    raise Exception("Max retries exceeded")


def pop_first_task():
    if not os.path.exists(QUEUE_FILE):
        return None

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return None

    first = lines[0]
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines[1:])

    return json.loads(first)


def append_failed(task, error):
    with open(FAILED_FILE, "a", encoding="utf-8") as f:
        task["error"] = str(error)
        f.write(json.dumps(task, ensure_ascii=False) + "\n")


# =========================
# Task Processor
# =========================

def process_task(client, task):
    try:
        if task["type"] != "local_file":
            return

        path = Path(task["path"])
        caption = task.get("caption", "")

        if not path.exists():
            raise Exception("File not found")

        send_with_retry(client, str(path), caption)

        # delete after success
        path.unlink(missing_ok=True)

    except Exception as e:
        append_failed(task, e)
        log("ERROR", "task_failed", error=str(e), task=task)
        traceback.print_exc()


# =========================
# Worker Loop
# =========================

def worker_loop():

    if not RUBIKA_SESSION:
        raise Exception("RUBIKA_SESSION not set")

    log("INFO", "worker_started")

    with RubikaClient(session=RUBIKA_SESSION) as client:

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

            while True:
                task = pop_first_task()

                if not task:
                    time.sleep(2)
                    continue

                executor.submit(process_task, client, task)


if __name__ == "__main__":
    worker_loop()
