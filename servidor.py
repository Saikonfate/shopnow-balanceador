import sys
import os
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
NOME = f"servidor-{PORTA}"

PRODUTOS = [
    {"id": 1, "nome": "Notebook Gamer", "preco": 4599.90},
    {"id": 2, "nome": "Smartphone", "preco": 1899.00},
    {"id": 3, "nome": "Fone Bluetooth", "preco": 249.90},
    {"id": 4, "nome": "Smart TV 50", "preco": 2299.00},
    {"id": 5, "nome": "Teclado Mecanico", "preco": 349.90},
]

contador = 0
lock = threading.Lock()


def pagina_inicial():
    itens = ""
    for p in PRODUTOS:
        itens += f"<li>{p['nome']} - R$ {p['preco']:.2f}</li>"
    return f"""<html>
<head><title>ShopNow</title></head>
<body>
<h1>ShopNow - Black Friday</h1>
<p>Atendido por: <b>{NOME}</b></p>
<p>Requisicoes atendidas por esta instancia: {contador}</p>
<ul>{itens}</ul>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global contador

        if self.path == "/health":
            self.responder(200, "text/plain", "ok")
            return

        if self.path == "/desligar":
            print(f"{NOME} foi desligado")
            self.responder(200, "text/plain", f"{NOME} desligando...")
            threading.Thread(target=desligar).start()
            return

        with lock:
            contador += 1

        time.sleep(0.02)

        if self.path == "/":
            self.responder(200, "text/html", pagina_inicial())
        elif self.path == "/produtos":
            dados = {"servidor": NOME, "produtos": PRODUTOS}
            self.responder(200, "application/json", json.dumps(dados))
        else:
            self.responder(404, "text/plain", "Pagina nao encontrada")

    def responder(self, status, tipo, texto):
        corpo = texto.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("X-Servidor", NOME)
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, format, *args):
        pass


def desligar():
    time.sleep(0.2)
    os._exit(0)


if __name__ == "__main__":
    ThreadingHTTPServer.request_queue_size = 128
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    print(f"{NOME} rodando em http://127.0.0.1:{PORTA}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print(f"{NOME} parado")
