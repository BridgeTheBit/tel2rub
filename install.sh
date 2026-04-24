#!/bin/bash

set -e

APP_NAME="tel2rub"
GITHUB_REPO="BridgeTheBit/tel2rub"

INSTALL_DIR="/opt/tel2rub"
BACKUP_DIR="/opt/tel2rub_backup"
SERVICE_NAME="tel2rub"
APP_USER="tel2rub"

GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
NC="\033[0m"

echo -e "${GREEN}=== Tel2Rub Installer ===${NC}"
echo

if [ "$EUID" -ne 0 ]; then
 echo -e "${RED}Please run with sudo${NC}"
 exit 1
fi

echo -e "${YELLOW}Installing dependencies...${NC}"
apt update -y
apt install -y python3 python3-venv python3-pip curl tar

echo -e "${YELLOW}Checking latest release...${NC}"
LATEST_TAG=$(curl -s https://api.github.com/repos/${GITHUB_REPO}/releases/latest | grep '"tag_name"' | cut -d '"' -f4)

if [ -z "$LATEST_TAG" ]; then
 echo -e "${RED}Failed to detect latest release${NC}"
 exit 1
fi

echo -e "${GREEN}Latest version: ${LATEST_TAG}${NC}"

INSTALLED_VERSION="none"
if [ -f "${INSTALL_DIR}/VERSION" ]; then
 INSTALLED_VERSION=$(cat ${INSTALL_DIR}/VERSION)
fi

echo -e "${YELLOW}Installed version: ${INSTALLED_VERSION}${NC}"

if [ "$INSTALLED_VERSION" == "$LATEST_TAG" ]; then
 echo -e "${GREEN}Already up to date${NC}"
 exit 0
fi

TMP_DIR=$(mktemp -d)

echo -e "${YELLOW}Downloading source...${NC}"
curl -L -o ${TMP_DIR}/source.tar.gz https://github.com/${GITHUB_REPO}/archive/refs/tags/${LATEST_TAG}.tar.gz
tar -xzf ${TMP_DIR}/source.tar.gz -C ${TMP_DIR}

NEW_SOURCE=$(find ${TMP_DIR} -maxdepth 1 -type d -name "tel2rub-*")

if [ -d "${INSTALL_DIR}" ]; then
 echo -e "${YELLOW}Creating backup...${NC}"
 rm -rf ${BACKUP_DIR}
 cp -r ${INSTALL_DIR} ${BACKUP_DIR}
fi

rollback() {
 echo -e "${RED}Installation failed. Rolling back...${NC}"
 rm -rf ${INSTALL_DIR}
 if [ -d "${BACKUP_DIR}" ]; then
  mv ${BACKUP_DIR} ${INSTALL_DIR}
 fi
 systemctl restart ${SERVICE_NAME} 2>/dev/null || true
 exit 1
}

trap rollback ERR

rm -rf ${INSTALL_DIR}
mv ${NEW_SOURCE} ${INSTALL_DIR}

cd ${INSTALL_DIR}

# ensure installer_session.py exists inside install folder
cp -f installer_session.py ${INSTALL_DIR}/

echo ${LATEST_TAG} > VERSION

echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

clear

# ------------------------------
# CREATE .env if missing
# ------------------------------
if [ ! -f "${INSTALL_DIR}/.env" ]; then
 echo -e "${GREEN}Creating .env file...${NC}"
 cat > ${INSTALL_DIR}/.env <<EOF
API_ID=
API_HASH=
BOT_TOKEN=
RUBIKA_SESSION=
EOF
fi

echo -e "${YELLOW}Configuring API credentials...${NC}"
read -p "API_ID: " API_ID
read -p "API_HASH: " API_HASH
read -p "BOT_TOKEN: " BOT_TOKEN

sed -i "s|API_ID=.*|API_ID=${API_ID}|g" ${INSTALL_DIR}/.env
sed -i "s|API_HASH=.*|API_HASH=${API_HASH}|g" ${INSTALL_DIR}/.env
sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=${BOT_TOKEN}|g" ${INSTALL_DIR}/.env

# --------------------------------
# SESSION CREATION / SELECTION
# --------------------------------
echo -e "${YELLOW}Setting up Rubika session...${NC}"

python3 installer_session.py || python installer_session.py

if [ $? -ne 0 ]; then
 echo -e "${RED}Rubika session creation failed${NC}"
 exit 1
fi

# --------------------------------
# CREATE SYSTEM USER
# --------------------------------
if ! id "$APP_USER" &>/dev/null; then
 echo -e "${YELLOW}Creating system user...${NC}"
 useradd -r -s /bin/false ${APP_USER}
fi

chown -R ${APP_USER}:${APP_USER} ${INSTALL_DIR}

# --------------------------------
# INSTALL CLI COMMAND
# --------------------------------
echo -e "${YELLOW}Installing CLI command...${NC}"
chmod -w ${INSTALL_DIR}/tel2rub
chmod +x ${INSTALL_DIR}/tel2rub
ln -sf ${INSTALL_DIR}/tel2rub /usr/local/bin/tel2rub

# --------------------------------
# CREATE SYSTEMD SERVICE
# --------------------------------
echo -e "${YELLOW}Installing systemd service...${NC}"

cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Tel2Rub Service
After=network.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

rm -rf ${TMP_DIR}

echo
echo -e "${GREEN}Installation complete!${NC}"
echo -e "${GREEN}Running version: ${LATEST_TAG}${NC}"
echo
echo "Manage using:"
echo "tel2rub"
echo
systemctl status tel2rub --no-pager
