#!/bin/bash

set -e

# ==============================
# CONFIG
# ==============================

GITHUB_REPO="BridgeTheBit/tel2rub"
INSTALL_DIR="/opt/tel2rub"
SERVICE_NAME="tel2rub"

# ==============================
# COLORS
# ==============================

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo -e "${GREEN}🚀 Tel2Rub Smart Installer${NC}"
echo

# ==============================
# CHECK ROOT
# ==============================

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (sudo)${NC}"
  exit 1
fi

# ==============================
# INSTALL DEPENDENCIES
# ==============================

echo -e "${YELLOW}📦 Installing dependencies...${NC}"
apt update -y
apt install -y python3 python3-venv python3-pip curl unzip

# ==============================
# GET LATEST RELEASE
# ==============================

echo -e "${YELLOW}🔎 Fetching latest release...${NC}"

LATEST_TAG=$(curl -s https://api.github.com/repos/${GITHUB_REPO}/releases/latest \
  | grep '"tag_name"' \
  | cut -d '"' -f4)

if [ -z "$LATEST_TAG" ]; then
  echo -e "${RED}❌ Could not fetch latest release.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Latest version: ${LATEST_TAG}${NC}"

# ==============================
# DOWNLOAD RELEASE
# ==============================

TMP_DIR=$(mktemp -d)

echo -e "${YELLOW}⬇ Downloading release...${NC}"

curl -L -o ${TMP_DIR}/source.tar.gz \
https://github.com/${GITHUB_REPO}/archive/refs/tags/${LATEST_TAG}.tar.gz

# ==============================
# EXTRACT
# ==============================

echo -e "${YELLOW}📂 Extracting...${NC}"

tar -xzf ${TMP_DIR}/source.tar.gz -C ${TMP_DIR}

EXTRACTED_DIR=$(find ${TMP_DIR} -maxdepth 1 -type d -name "tel2rub-*")

rm -rf ${INSTALL_DIR}
mv ${EXTRACTED_DIR} ${INSTALL_DIR}

# ==============================
# SETUP VENV
# ==============================

echo -e "${YELLOW}🐍 Setting up virtual environment...${NC}"

cd ${INSTALL_DIR}
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ==============================
# CREATE .env
# ==============================

echo
echo -e "${GREEN}⚙ Configure Tel2Rub${NC}"

read -p "API_ID: " API_ID
read -p "API_HASH: " API_HASH
read -p "BOT_TOKEN: " BOT_TOKEN
read -p "RUBIKA_SESSION: " RUBIKA_SESSION

cat > ${INSTALL_DIR}/.env <<EOF
API_ID=${API_ID}
API_HASH=${API_HASH}
BOT_TOKEN=${BOT_TOKEN}
RUBIKA_SESSION=${RUBIKA_SESSION}
EOF

# ==============================
# INSTALL SERVICE
# ==============================

echo -e "${YELLOW}🔧 Installing systemd service...${NC}"

cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Tel2Rub Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

# ==============================
# CLEANUP
# ==============================

rm -rf ${TMP_DIR}

echo
echo -e "${GREEN}✅ Tel2Rub ${LATEST_TAG} installed successfully!${NC}"
echo -e "${GREEN}Service started and enabled on boot.${NC}"
echo
echo "Use:"
echo "  systemctl status tel2rub"
echo
