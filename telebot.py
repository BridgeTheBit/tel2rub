import os, json, asyncio
from pathlib import Path
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID",0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

QUEUE = Path("queue")
DOWNLOADS = Path("downloads")
QUEUE.mkdir(exist_ok=True)
DOWNLOADS.mkdir(exist_ok=True)

TASK_FILE = QUEUE / "tasks.jsonl"

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def append_task(task):
    with open(TASK_FILE, "a") as f:
        f.write(json.dumps(task)+"
")

@app.on_message(filters.document | filters.video | filters.audio)
async def media_handler(client, message):
    status = await message.reply_text("Downloading...")

    path = await message.download(file_name=str(DOWNLOADS))

    size = Path(path).stat().st_size

    await status.edit_text(f"Downloaded: {Path(path).name} ({size} bytes)")

    task = {
        "file_path": path,
        "chat_id": message.chat.id,
        "caption": message.caption or ""
    }

    append_task(task)

    await message.reply_text("Added to upload queue.")

app.run()
