import subprocess, sys

procs = []

try:
    procs.append(subprocess.Popen([sys.executable, "telebot.py"]))
    procs.append(subprocess.Popen([sys.executable, "rub.py"]))

    for p in procs:
        p.wait()
except KeyboardInterrupt:
    for p in procs:
        p.kill()
