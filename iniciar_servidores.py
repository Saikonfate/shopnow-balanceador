import sys
import subprocess
import time

PORTAS = [5001, 5002, 5003]

processos = []
for porta in PORTAS:
    p = subprocess.Popen([sys.executable, "servidor.py", str(porta)])
    processos.append(p)

print(f"{len(PORTAS)} servidores iniciados. Ctrl+C para parar todos.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for p in processos:
        p.terminate()
    print("Servidores parados")
