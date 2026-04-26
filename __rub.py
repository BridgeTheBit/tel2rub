import os
import re
import json
import time
import uuid
import zipfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rubpy import Client as RubikaClient


load_dotenv()

SESSION = os.getenv("RUBIKA_SESSION", "rubika_session").strip()

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
QUEUE_DIR = BASE_DIR / "queue"
QUEUE_FILE = QUEUE_DIR / "tasks.jsonl"
PROCESSING_FILE = QUEUE_DIR / "processing.json"
FAILED_FILE = QUEUE_DIR / "failed.jsonl"

MAX_RETRIES = 5
RETRY_DELAY = 3
TARGET = "me"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

client = None  # ✅ persistent client


# -------------------------
# Utils
# -------------------------

def safe_filename(name: Optional[str]) -> str:
    name = (name or "file").strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = name.rstrip(". ")
    return name[:200] or "file"


def has_session(session_name: str) -> bool:
    return any(
        Path(p).exists()
        for p in [
            session_name,
            f"{session_name}.session",
            f"{session_name}.sqlite",
        ]
    )


# -------------------------
# Client
# -------------------------

def init_client():
    global client

    if client is not None:
        return client

    if not has_session(SESSION):
        raise RuntimeError("Run installer_session.py first.")

    client = RubikaClient(name=SESSION)

    client.start()
    print("✅ Rubika connected.")

    return client


def reconnect():
    global client

    try:
        if client:
            client.disconnect()
    except:
        pass

    client = None
    time.sleep(1)
    return init_client()


# -------------------------
# ZIP (🔥 مهم‌ترین تغییر)
# -------------------------

def create_zip(file_path: Path) -> Path:
    zip_name = f"{file_path.stem}_{uuid.uuid4().hex}.zip"
    zip_path = file_path.parent / zip_name

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, arcname=file_path.name)

    return zip_path


# -------------------------
# Send
# -------------------------

def send_document(file_path: str):
    global client

    return client.send_document(
        TARGET,
        file_path,
        caption=""  # ✅ کپشن حذف شد
    )


def send_with_retry(file_path: str):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return send_document(file_path)

        except Exception as e:
            last_error = e
            error_text = str(e).lower()

            if "session" in error_text or "not authorized" in error_text:
                reconnect()
                continue

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue

            break

    raise last_error


# -------------------------
# Queue
# -------------------------

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


def process_task(task: dict):
    original_path = Path(task["path"])

    if not original_path.exists():
        raise RuntimeError("File not found")

    # ✅ ZIP یونیک
    zip_path = create_zip(original_path)

    try:
        send_with_retry(str(zip_path))
    finally:
        if zip_path.exists():
            zip_path.unlink()


# -------------------------
# Worker
# -------------------------

def worker_loop():
    init_client()
    print("🚀 Worker started")

    while True:
        task = pop_first_task()

        if not task:
            time.sleep(0.2)
            continue

        try:
            process_task(task)
        except Exception as e:
            print("❌ Error:", e)


if __name__ == "__main__":
    worker_loop()
