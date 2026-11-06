import sys
import threading
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTA = 8080

SERVIDORES = [
    {"url": "http://127.0.0.1:5001", "conexoes": 0, "atendidas": 0},
    {"url": "http://127.0.0.1:5002", "conexoes": 0, "atendidas": 0},
    {"url": "http://127.0.0.1:5003", "conexoes": 0, "atendidas": 0},
]

lock = threading.Lock()
indice_atual = 0


def round_robin():
    global indice_atual
    with lock:
        servidor = SERVIDORES[indice_atual % len(SERVIDORES)]
        indice_atual += 1
        return servidor


def menos_conexoes():
    with lock:
        return min(SERVIDORES, key=lambda s: s["conexoes"])


ALGORITMOS = {
    "round_robin": round_robin,
    "menos_conexoes": menos_conexoes,
}

nome_algoritmo = sys.argv[1] if len(sys.argv) > 1 else "round_robin"
if nome_algoritmo not in ALGORITMOS:
    print(f"Algoritmo invalido. Opcoes: {', '.join(ALGORITMOS)}")
    sys.exit(1)
escolher_servidor = ALGORITMOS[nome_algoritmo]


class Balanceador(BaseHTTPRequestHandler):
    def do_GET(self):
        servidor = escolher_servidor()
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
        finally:
            with lock:
                servidor["conexoes"] -= 1

        with lock:
            servidor["atendidas"] += 1

        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("X-Servidor", servidor["url"])
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer.request_queue_size = 128
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Balanceador)
    print(f"Balanceador rodando em http://127.0.0.1:{PORTA} ({nome_algoritmo})")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Balanceador parado")
