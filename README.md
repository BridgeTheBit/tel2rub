# rubikaTeleporter
A Telegram bot that downloads files, compresses them with password protection, splits large files, and automatically uploads them to Rubika.


Telegram → Rubika automatic file transfer bot.

This project downloads files from Telegram, compresses them with password protection, splits large files, and uploads them to Rubika automatically.

## Features

- Telegram file downloader
- Automatic ZIP compression
- Random password protection
- Split files larger than 100MB
- Upload to Rubika
- Queue system
- Retry on upload failure
- Systemd service support

## Installation
```bash
pip install -r requirements.txt
python3 main.py
