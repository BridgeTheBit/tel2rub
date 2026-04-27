import os
import re
import json
import time
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

client = None  # 🔥 global persistent client


KEEP_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v",
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp",
    ".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".pdf", ".txt", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}


# -------------------------
# Utils
# -------------------------

def safe_filename(name: Optional[str]) -> str:
    name = (name or "file").strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = name.rstrip(". ")
    return name[:200] or "file"


def remove_extension(name: str) -> str:
    name = safe_filename(name)
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name or "file"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    index = 1

    while True:
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


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
# Client مدیریت اتصال
# -------------------------

def init_client():
    global client

    if client is not None:
        return client

    if not has_session(SESSION):
        raise RuntimeError(
            "Rubika session not found. Run installer_session.py first."
        )

    client = RubikaClient(name=SESSION)

    try:
        client.start()
        print("✅ Rubika connected.")
    except Exception as e:
        print("❌ Failed to connect:", e)
        raise

    return client


def reconnect():
    global client

    try:
        if client:
            client.disconnect()
    except Exception:
        pass

    client = None
    time.sleep(1)

    print("🔄 Reconnecting...")
    return init_client()


# -------------------------
# Send
# -------------------------

def send_document(file_path: str, caption: str = ""):
    global client

    if client is None:
        raise RuntimeError("Client not initialized")

    return client.send_document(
        TARGET,
        file_path,
        caption=caption or ""
    )


def send_with_retry(file_path: str, caption: str = ""):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return send_document(file_path, caption)

        except Exception as e:
            last_error = e
            error_text = str(e).lower()

            # 🔥 اگر سشن پرید → reconnect
            if any(k in error_text for k in ["session", "not authorized", "login"]):
                reconnect()
                continue

            transient = any(
                key in error_text
                for key in [
                    "502",
                    "bad gateway",
                    "timeout",
                    "cannot connect",
                    "connection reset",
                    "temporarily unavailable",
                    "error uploading chunk",
                ]
            )

            if transient and attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue

            break

    raise last_error if last_error else RuntimeError("Upload failed.")


# -------------------------
# Queue
# -------------------------

def pop_first_task():
    if not QUEUE_FILE.exists():
        return None

    with open(QUEUE_FILE, "r", encoding="utf-8") as file:
        lines = [line for line in file if line.strip()]

    if not lines:
        return None

    first_line = lines[0]
    remaining = lines[1:]

    with open(QUEUE_FILE, "w", encoding="utf-8") as file:
        file.writelines(remaining)

    return json.loads(first_line)


def save_processing(task: dict) -> None:
    with open(PROCESSING_FILE, "w", encoding="utf-8") as file:
        json.dump(task, file, ensure_ascii=False, indent=2)


def clear_processing() -> None:
    if PROCESSING_FILE.exists():
        PROCESSING_FILE.unlink()


def append_failed(task: dict, error: str) -> None:
    payload = {"task": task, "error": error}
    with open(FAILED_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


# -------------------------
# Task processing
# -------------------------

def should_keep_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in KEEP_EXTENSIONS


def process_task(task: dict):
    task_type = task.get("type")
    caption = task.get("caption", "")

    if task_type != "local_file":
        raise RuntimeError("Unknown task type.")

    original_path = Path(task.get("path", ""))
    if not original_path.exists():
        raise RuntimeError("Local file not found.")

    if should_keep_extension(original_path.name):
        send_path = original_path
    else:
        clean_name = remove_extension(original_path.name)
        send_path = unique_path(original_path.parent / clean_name)

        try:
            original_path.rename(send_path)
        except Exception:
            send_path = original_path

    try:
        send_with_retry(str(send_path), caption)
    finally:
        try:
            if send_path.exists():
                send_path.unlink()
        except Exception:
            pass


# -------------------------
# Worker
# -------------------------

def worker_loop():
    init_client()
    print("🚀 Rubika worker started.")

    while True:
        task = pop_first_task()

        if not task:
            time.sleep(0.2)
            continue

        save_processing(task)

        try:
            process_task(task)
        except Exception as e:
            append_failed(task, str(e))
        finally:
            clear_processing()


if __name__ == "__main__":
    worker_loop()
