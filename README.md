# ShopNow - Balanceador de Carga

Trabalho da disciplina de Sistemas Distribuídos.

A ShopNow é uma loja online que cresceu e começou a ter lentidão e quedas em dias de promoção (tipo Black Friday), porque tudo rodava em um único servidor. A solução foi colocar **várias instâncias do site** rodando ao mesmo tempo e um **balanceador de carga** na frente, que distribui as requisições entre elas.

Tudo foi feito em Python, usando só a biblioteca padrão (não precisa instalar nada).

## Arquitetura

```
                    +-------------------+
                    |   Cliente / ab    |
                    +---------+---------+
                              |
                              v
                 +------------------------+
                 |  Balanceador (:8080)   |
                 |  round robin ou        |
                 |  menos conexões        |
                 +---+--------+--------+--+
                     |        |        |
                     v        v        v
                 +------+ +------+ +------+
                 | 5001 | | 5002 | | 5003 |
                 +------+ +------+ +------+
                  Instâncias do site ShopNow
```

## Arquivos

| Arquivo | O que faz |
|---|---|
| `servidor.py` | Uma instância do site da loja. Recebe a porta como parâmetro. |
| `iniciar_servidores.py` | Sobe as 3 instâncias de uma vez (portas 5001, 5002 e 5003). |
| `balanceador.py` | O balanceador de carga, roda na porta 8080. |
| `simular_falha.py` | Manda requisições e derruba um servidor no meio para ver o que acontece. |

## Rotas

**Servidores (5001, 5002, 5003)**

- `/` - página inicial da loja (mostra qual instância atendeu)
- `/produtos` - lista de produtos em JSON
- `/health` - usado pelo balanceador para saber se o servidor está vivo
- `/desligar` - derruba o servidor (usado para simular falha)

**Balanceador (8080)**

- Qualquer rota é repassada para um dos servidores
- `/status` - mostra o algoritmo em uso e a situação de cada servidor (ativo, conexões abertas e requisições atendidas)

Toda resposta tem o cabeçalho `X-Servidor` dizendo qual instância respondeu.

## Algoritmos implementados

### Round Robin

Manda cada requisição para o próximo servidor da lista, em ordem circular: 5001 → 5002 → 5003 → 5001 → ...
É simples e funciona bem quando todos os servidores têm a mesma capacidade.

### Menos conexões (Least Connections)

O balanceador guarda quantas requisições cada servidor está atendendo naquele momento e manda a nova para o que estiver **menos ocupado**. É melhor quando algumas requisições demoram mais que outras, porque evita sobrecarregar um servidor que ficou "preso".

## Como rodar

Precisa do Python 3.8 ou mais novo.

**1. Subir as instâncias** (terminal 1)

```bash
python iniciar_servidores.py
```

Ou subir uma por uma, cada uma em um terminal:

```bash
python servidor.py 5001
python servidor.py 5002
python servidor.py 5003
```

**2. Subir o balanceador** (terminal 2), escolhendo o algoritmo:

```bash
python balanceador.py round_robin
```

ou

```bash
python balanceador.py menos_conexoes
```

**3. Acessar**

Abrir http://127.0.0.1:8080 no navegador e ir atualizando a página. O nome do servidor que atendeu vai mudando.

Para ver o status: http://127.0.0.1:8080/status

## Tolerância a falhas

O balanceador trata a queda de servidores de dois jeitos:

1. **Health check**: a cada 2 segundos ele chama `/health` em todos os servidores. Se algum não responder, é marcado como `OFFLINE` e para de receber requisições. Quando volta a responder, é marcado como `ONLINE` de novo automaticamente.
2. **Nova tentativa**: se uma requisição for enviada para um servidor que acabou de cair (antes do health check perceber), o balanceador marca ele como offline e tenta em outro servidor. Assim o cliente não recebe erro.

Se **todos** os servidores caírem, o balanceador responde `503 - Nenhum servidor disponivel`.

### Simulando uma falha

Com os servidores e o balanceador rodando:

```bash
python simular_falha.py
```

O script manda 30 requisições e, na 10ª, derruba o servidor 5002. Dá para ver que depois disso as requisições passam a ir só para o 5001 e o 5003, sem nenhum erro. No terminal do balanceador aparece:

```
[ERRO] http://127.0.0.1:5002 falhou, tentando outro servidor
[OFFLINE] http://127.0.0.1:5002 parou de responder
```

Também dá para derrubar manualmente com `curl http://127.0.0.1:5002/desligar` ou só fechando o terminal do servidor (Ctrl+C).

Para o servidor voltar, é só subir ele de novo:

```bash
python servidor.py 5002
```

Em até 2 segundos o balanceador mostra `[ONLINE] http://127.0.0.1:5002 voltou a responder`.

## Teste de carga com Apache Benchmark (ab)

O `ab` vem junto com o Apache. No Linux: `sudo apt install apache2-utils`. No Windows dá para pegar o `ab.exe` na pasta `bin` do Apache (Apache Lounge ou XAMPP).

**1000 requisições, 50 simultâneas, passando pelo balanceador:**

```bash
ab -n 1000 -c 50 http://127.0.0.1:8080/
```

**Comparando com um servidor sozinho (sem balanceador):**

```bash
ab -n 1000 -c 50 http://127.0.0.1:5001/
```

**Teste de carga com falha no meio:** rodar o `ab` com mais requisições e, enquanto ele roda, derrubar um servidor em outro terminal:

```bash
ab -n 5000 -c 100 http://127.0.0.1:8080/
```

```bash
curl http://127.0.0.1:5002/desligar
```

No final, olhar o campo `Failed requests` do `ab` e o `/status` do balanceador para ver como as requisições foram distribuídas.

Também dá para usar o `wrk` (Linux/Mac):

```bash
wrk -t4 -c100 -d30s http://127.0.0.1:8080/
```

## O que observar nos testes

- Com **round robin**, o `/status` mostra as requisições divididas quase igualmente entre os 3 servidores.
- Com **menos conexões**, a divisão também fica equilibrada, mas se um servidor ficar mais lento ele recebe menos requisições.
- Quando um servidor cai, os outros assumem a carga e o `ab` continua sem (ou com pouquíssimas) falhas.
- Cada servidor tem um pequeno atraso proposital (20ms) para simular o processamento de uma página real.

## Autor

Wesley Furtado Pessoa
