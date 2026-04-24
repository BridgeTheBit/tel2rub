#!/bin/bash

sudo apt update
sudo apt install python3 python3-pip -y

pip3 install -r requirements.txt

mkdir -p downloads queue logs

sudo cp service/tel2rub.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable tel2rub
sudo systemctl start tel2rub
