import sys
import json
import time
import threading
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTA = 8080
INTERVALO_HEALTH_CHECK = 2

SERVIDORES = [
    {"url": "http://127.0.0.1:5001", "ativo": True, "conexoes": 0, "atendidas": 0},
    {"url": "http://127.0.0.1:5002", "ativo": True, "conexoes": 0, "atendidas": 0},
    {"url": "http://127.0.0.1:5003", "ativo": True, "conexoes": 0, "atendidas": 0},
]

lock = threading.Lock()
indice_atual = 0


def servidores_ativos():
    return [s for s in SERVIDORES if s["ativo"]]


def round_robin():
    global indice_atual
    with lock:
        ativos = servidores_ativos()
        if not ativos:
            return None
        servidor = ativos[indice_atual % len(ativos)]
        indice_atual += 1
        return servidor


def menos_conexoes():
    with lock:
        ativos = servidores_ativos()
        if not ativos:
            return None
        return min(ativos, key=lambda s: s["conexoes"])


ALGORITMOS = {
    "round_robin": round_robin,
    "menos_conexoes": menos_conexoes,
}

nome_algoritmo = sys.argv[1] if len(sys.argv) > 1 else "round_robin"
if nome_algoritmo not in ALGORITMOS:
    print(f"Algoritmo invalido. Opcoes: {', '.join(ALGORITMOS)}")
    sys.exit(1)
escolher_servidor = ALGORITMOS[nome_algoritmo]


def marcar_servidor(servidor, ativo):
    if servidor["ativo"] != ativo:
        if ativo:
            print(f"[ONLINE]  {servidor['url']} voltou a responder")
        else:
            print(f"[OFFLINE] {servidor['url']} parou de responder")
    servidor["ativo"] = ativo


def health_check():
    while True:
        for servidor in SERVIDORES:
            try:
                urllib.request.urlopen(servidor["url"] + "/health", timeout=1)
                marcar_servidor(servidor, True)
            except Exception:
                marcar_servidor(servidor, False)
        time.sleep(INTERVALO_HEALTH_CHECK)


class Balanceador(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            self.mostrar_status()
            return

        if self.path == "/desligar":
            self.responder(403, "text/plain; charset=utf-8", b"Acesso negado", "balanceador")
            return

        for tentativa in range(len(SERVIDORES)):
            servidor = escolher_servidor()
            if servidor is None:
                break

            with lock:
                servidor["conexoes"] += 1
            try:
                resposta = urllib.request.urlopen(servidor["url"] + self.path, timeout=3)
                status = resposta.status
                tipo = resposta.headers.get("Content-Type", "text/html")
                corpo = resposta.read()
            except urllib.error.HTTPError as e:
                status = e.code
                tipo = e.headers.get("Content-Type", "text/plain")
                corpo = e.read()
            except Exception:
                print(f"[ERRO] {servidor['url']} falhou, tentando outro servidor")
                marcar_servidor(servidor, False)
                continue
            finally:
                with lock:
                    servidor["conexoes"] -= 1

            with lock:
                servidor["atendidas"] += 1
            self.responder(status, tipo, corpo, servidor["url"])
            return

        self.responder(503, "text/plain; charset=utf-8", "Nenhum servidor disponivel".encode("utf-8"), "nenhum")

    def mostrar_status(self):
        dados = {
            "algoritmo": nome_algoritmo,
            "servidores": SERVIDORES,
        }
        corpo = json.dumps(dados, indent=2).encode("utf-8")
        self.responder(200, "application/json", corpo, "balanceador")

    def responder(self, status, tipo, corpo, origem):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("X-Servidor", origem)
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=health_check, daemon=True).start()

    ThreadingHTTPServer.request_queue_size = 128
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Balanceador)
    print(f"Balanceador rodando em http://127.0.0.1:{PORTA} ({nome_algoritmo})")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Balanceador parado")
