import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from rubpy import Client as RubikaClient
import requests  # for telegram bot notify


# ================================================================
# ENV
# ================================================================
load_dotenv()

SESSION = os.getenv("RUBIKA_SESSION", "rubika_session")
TARGET = "me"

# Telegram bot notifications
BOT_TOKEN = os.getenv("BOT_TOKEN")              # توکن ربات
ADMIN_ID = os.getenv("ADMIN_ID")                # چت آی‌دی ادمین

MAX_RETRIES = 5
RETRY_DELAY = 3


# ================================================================
# PATHS
# ================================================================
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
QUEUE_DIR = BASE_DIR / "queue"

QUEUE_FILE = QUEUE_DIR / "tasks.jsonl"
FAILED_FILE = QUEUE_DIR / "failed.jsonl"

LOG_DIR.mkdir(exist_ok=True)
QUEUE_DIR.mkdir(parents=True, exist_ok=True)


# ================================================================
# LOGGER (English only)
# ================================================================
logging.basicConfig(
    filename=LOG_DIR / "worker.log",
    filemode="a",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)


def log(level, msg, **extra):
    """English structured logs."""
    payload = {"msg": msg, **extra}
    logging.log(level, json.dumps(payload))


# ================================================================
# TELEGRAM NOTIFY (PERSIAN)
# ================================================================
def notify_telegram(text: str):
    if not BOT_TOKEN or not ADMIN_ID:
        return
    try:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={
                "chat_id": ADMIN_ID,
                "text": text,
            },
            timeout=10
        )
    except:
        pass


# ================================================================
# GLOBAL CLIENT (Singleton)
# ================================================================
client: Optional[RubikaClient] = None


def get_client() -> RubikaClient:
    global client
    if client is None:
        client = RubikaClient(name=SESSION)
        client.start()
        log(logging.INFO, "Rubika session started")
    return client


def close_client():
    global client
    if client:
        try:
            client.disconnect()
        except:
            pass
        client = None


# ================================================================
# FILE HELPERS
# ================================================================
def safe_filename(name: Optional[str]) -> str:
    name = (name or "file").strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = name.rstrip(". ")
    return name[:200] or "file"


# ================================================================
# SEND FILE
# ================================================================
def send_document(path: str, caption: str = ""):
    rub = get_client()
    return rub.send_document(TARGET, path, caption=caption or "")


def send_with_retry(path: str, caption: str = ""):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(logging.INFO, "Uploading file", attempt=attempt, file=path)
            return send_document(path, caption)

        except Exception as e:
            last_error = e
            err = str(e).lower()

            transient = any(key in err for key in [
                "timeout",
                "502",
                "bad gateway",
                "temporarily",
                "error uploading chunk",
            ])

            if transient and attempt < MAX_RETRIES:
                delay = RETRY_DELAY * attempt
                log(logging.WARNING, "Transient error, retrying",
                    error=str(e), wait=delay)
                time.sleep(delay)
                continue

            break

    log(logging.ERROR, "Upload failed", error=str(last_error), file=path)
    raise last_error


# ================================================================
# QUEUE HANDLING
# ================================================================
def pop_first_task():
    if not QUEUE_FILE.exists():
        return None

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]

    if not lines:
        return None

    first = lines[0]
    rest = lines[1:]

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.writelines(rest)

    return json.loads(first)


def save_failed(task, error):
    payload = {"task": task, "error": error}
    with open(FAILED_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


# ================================================================
# PROCESSOR
# ================================================================
def process_task(task: dict):
    file_path = Path(task.get("path"))
    caption = task.get("caption", "")

    if not file_path.exists():
        raise RuntimeError("File not found")

    send_with_retry(str(file_path), caption)

    try:
        file_path.unlink()
    except:
        pass


# ================================================================
# WORKER LOOP
# ================================================================
def worker_loop():
    log(logging.INFO, "Worker started")
    get_client()

    notify_telegram("🔵 ورکر روبیکا با موفقیت شروع شد.")

    while True:
        task = pop_first_task()

        if not task:
            time.sleep(0.2)
            continue

        file_name = Path(task["path"]).name

        try:
            notify_telegram(f"⏳ در حال ارسال فایل:\n{file_name}")
            process_task(task)

            notify_telegram(
                f"✅ فایل با موفقیت ارسال شد:\n{file_name}"
            )
            log(logging.INFO, "Upload success", file=file_name)

        except Exception as e:
            err = str(e)
            save_failed(task, err)

            notify_telegram(
                f"❌ خطا در ارسال فایل:\n{file_name}\n\n"
                f"متن خطا:\n{err}"
            )

            log(logging.ERROR, "Upload failed", file=file_name, error=err)


# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    worker_loop()
