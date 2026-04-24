import os
import json
import random
import string
import zipfile
import logging
from pathlib import Path
from pyrogram import Client, filters
from dotenv import load_dotenv

# ---------- تنظیمات اولیه ---------- #
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "@rubika_target")

QUEUE = Path("queue")
DOWNLOADS = Path("downloads")
LOGS = Path("logs")
MAX_SIZE = 100 * 1024 * 1024  # 100MB

for p in [QUEUE, DOWNLOADS, LOGS]:
    p.mkdir(exist_ok=True)

TASK_FILE = QUEUE / "tasks.jsonl"
LOG_FILE = LOGS / "app.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [TELEBOT] %(levelname)s: %(message)s",
)

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- کمکی‌ها ---------- #
def random_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def append_task(task: dict):
    with open(TASK_FILE, "a") as f:
        f.write(json.dumps(task) + "\n")

def split_file(file_path: Path, chunk_size=MAX_SIZE):
    parts = []
    with open(file_path, "rb") as f:
        idx = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            part_path = file_path.parent / f"{file_path.stem}_part{idx}{file_path.suffix}"
            with open(part_path, "wb") as part_file:
                part_file.write(chunk)
            parts.append(part_path)
            idx += 1
    return parts

# ---------- هندلر پیام‌ها ---------- #
@app.on_message(filters.document | filters.video | filters.audio)
async def media_handler(client, message):
    try:
        status = await message.reply_text("📥 در حال دانلود فایل ...")

        # دانلود فایل
        file_path = await message.download(file_name=str(DOWNLOADS))
        file_path = Path(file_path)
        size = file_path.stat().st_size

        # تقسیم فایل‌های بزرگ
        if size > MAX_SIZE:
            await status.edit_text("🔪 فایل بزرگ است، در حال تقسیم به چند بخش ...")
            parts = split_file(file_path)
            os.remove(file_path)
        else:
            parts = [file_path]

        await status.edit_text(f"📦 {len(parts)} بخش آماده شد، در حال فشرده‌سازی ...")

        zipped_files = []
        for part in parts:
            password = random_password(8)
            zip_path = part.with_suffix(".zip")

            # ساخت فایل ZIP رمزدار
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(part, arcname=part.name)
                z.setpassword(password.encode())

            zipped_files.append((zip_path, password))
            os.remove(part)

        await status.edit_text("📨 در حال ارسال فایل‌ها به صف آپلود ...")

        # اضافه به صف روبیکا
        for zip_path, password in zipped_files:
            append_task({
                "file_path": str(zip_path),
                "target": TARGET_CHANNEL,
                "caption": f"{message.caption or ''}\n\nPassword: `{password}`"
            })

            await message.reply_text(
                f"📤 فایل {zip_path.name} به صف اضافه شد.\n🔑 رمز: `{password}`",
                quote=True
            )

        await status.delete()
        logging.info(f"Queued {len(zipped_files)} file(s) from user {message.from_user.id}")

    except Exception as e:
        await message.reply_text(f"❌ خطا: {e}")
        logging.error(f"Error: {e}")

# ---------- اجرای بات ---------- #
app.run()
