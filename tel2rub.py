#!/usr/bin/env python3
import os

while True:
    print("""
1 status
2 logs
3 restart
4 stop
5 exit
""")

    c = input("choice: ")

    if c == "1":
        os.system("systemctl status tel2rub")

    elif c == "2":
        os.system("tail -f logs/app.log")

    elif c == "3":
        os.system("sudo systemctl restart tel2rub")

    elif c == "4":
        os.system("sudo systemctl stop tel2rub")

    elif c == "5":
        break
