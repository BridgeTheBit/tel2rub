[فارسی](https://github.com/BridgeTheBit/tel2rub/edit/main/README_FA.md)
# 🚀 Tel2Rub — Telegram to Rubika Bridge

**Tel2Rub** is a professional message‑sync tool that forwards Telegram messages directly into Rubika.  
It focuses on stability, fully automated Rubika session handling, simple installation, and a powerful CLI tool.

---

# ✨ Features

### 🔹 Telegram → Rubika Message Sync  
Automatically forwards messages from a Telegram chat / group / channel into Rubika.

### 🔹 Fully Automated Rubika Session Handling
- Detects existing session  
- Option to reuse or create a new session  
- Handles phone number login + verification code  
- Saves the `rubika.session` file  
- Updates `.env` automatically  

### 🔹 One‑Command Installer
Everything is installed automatically with a single command.

### 🔹 Auto‑Updater
Running the installer again → updates the app if a new version exists.

### 🔹 Built‑in CLI
Accessible globally via:


---

# 🛠️ Installation

Install the entire application with **one command**:
```bash
bash <(curl -s https://raw.githubusercontent.com/BridgeTheBit/tel2rub/main/install.sh)
```

The installer will:
- Fetch the latest release
- Create /opt/tel2rub
- Create virtual environment
- Install all dependencies
- Generate .env
- Ask for Telegram API keys and Bot Token
- Run full Rubika session authentication
- Create and enable systemd service
- Install global CLI command

# 🔄 Update
Update by running the same command again:

```bash
bash <(curl -s https://raw.githubusercontent.com/BridgeTheBit/tel2rub/main/install.sh)
```

- If a new version is available → update happens automatically
- If already up‑to‑date → installer prints “Already up to date”

# 📂 Project Structure
```text
/opt/tel2rub
 ├── install.sh
 ├── installer_session.py
 ├── requirements.txt
 ├── main.py
 ├── rub.py
 ├── telebot.py
 ├── tel2rub
 ├── VERSION
 ├── .env
 └── venv/
```

# File Descriptions
- main.py → main app entry
- rub.py → Rubika API logic
- telebot.py → Telegram bot handler
- installer_session.py → automated Rubika session creator
- tel2rub → global CLI tool
- VERSION → installed version string
- .env → environment & credentials

# ▶️ Running the Application
The service starts automatically after installation:

```bash
systemctl status tel2rub
```

# CLI menu:

```bash
tel2rub
```

# 🧰 CLI Commands
```bash
tel2rub start
tel2rub stop
tel2rub restart
tel2rub logs
```

# ❤️ Contributing
If you find this project useful, please ⭐ star the repository and contribute!
