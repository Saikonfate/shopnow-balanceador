import time
import urllib.request
from collections import Counter

BALANCEADOR = "http://127.0.0.1:8080"
SERVIDOR_QUE_VAI_CAIR = "http://127.0.0.1:5002"
TOTAL_REQUISICOES = 30
DERRUBAR_NA = 10


def fazer_requisicao():
    try:
        resposta = urllib.request.urlopen(BALANCEADOR + "/", timeout=5)
        return resposta.headers.get("X-Servidor")
    except Exception:
        return "ERRO"


print(f"Enviando {TOTAL_REQUISICOES} requisicoes para o balanceador...\n")

contagem = Counter()
for i in range(1, TOTAL_REQUISICOES + 1):
    if i == DERRUBAR_NA:
        print(f"\n>>> Derrubando {SERVIDOR_QUE_VAI_CAIR}\n")
        urllib.request.urlopen(SERVIDOR_QUE_VAI_CAIR + "/desligar")
        time.sleep(0.5)

    quem_respondeu = fazer_requisicao()
    contagem[quem_respondeu] += 1
    print(f"Requisicao {i:2d} -> {quem_respondeu}")
    time.sleep(0.1)

print("\nResumo:")
for servidor, qtd in contagem.items():
    print(f"  {servidor}: {qtd}")
