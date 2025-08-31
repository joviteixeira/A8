# README — Projeto de Microservices

Este repositório contém **duas versões** do mesmo sistema de pedidos, usadas para fins didáticos:

- `/versao_inicial/` — implementação **intencionalmente frágil** (anti-patterns).
- `/versao_refatorada/` — implementação **refatorada com padrões** (API Gateway, Circuit Breaker, Bulkhead e IoC).

> Requisitos: Docker e Docker Compose (v2).  
> Como rodar cada versão: entre na pasta correspondente e execute `docker compose up --build`.

---

# /versao_inicial

Sistema com **5 microserviços** em Flask, **acoplados diretamente** via HTTP com URLs hardcoded, **sem** timeouts/retries, **sem** descoberta de serviço, **sem** orquestração resiliente.

## Serviços

| Serviço   | Porta host | Principais rotas                         |
|-----------|------------|------------------------------------------|
| user      | 5001       | `GET /health`, `GET /users/:id`, `POST /users` |
| inventory | 5002       | `GET /health`, `GET /stock/:sku`, `POST /reserve` |
| payment   | 5003       | `GET /health`, `POST /pay`               |
| shipping  | 5004       | `GET /health`, `POST /ship`              |
| order     | 5005       | `GET /health`, `GET /orders/:id`, `POST /orders` |

## Subir os serviços

```bash
cd versao_inicial
docker compose up --build
```

Health checks:

```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
curl http://localhost:5004/health
curl http://localhost:5005/health
```

## Fluxo de teste rápido

1) Ver estoque:

```bash
curl http://localhost:5002/stock/SKU-001
```

2) Criar pedido (o **order** chama **user → inventory → payment → shipping** de forma **síncrona e direta**):

```bash
curl -X POST http://localhost:5005/orders   -H "Content-Type: application/json"   -d '{
    "user_id": 1,
    "items": [{"product_id": "SKU-001", "qty": 1}],
    "address": "Rua Exemplo, 100 - Santo Antônio de Jesus/BA"
  }'
```

3) Buscar pedido criado:

```bash
curl http://localhost:5005/orders/1
```

## Anti-patterns propositalmente presentes

- **Acoplamento rígido**: URLs dos serviços estão hardcoded no serviço `order`.
- **Chamadas síncronas em cascata** sem fallback.
- **Sem timeouts/retries** (falhas propagam).
- **God Service**: `order` concentra regras e orquestra tudo.
- **Sem idempotência/rollback**: reserva de estoque sem compensação.

## Estrutura

```
versao_inicial/
  docker-compose.yml
  README.md
  services/
    user/       (app.py, Dockerfile, requirements.txt)
    inventory/  (app.py, Dockerfile, requirements.txt)
    payment/    (app.py, Dockerfile, requirements.txt)
    shipping/   (app.py, Dockerfile, requirements.txt)
    order/      (app.py, Dockerfile, requirements.txt)
```


# /versao_refatorada

Versão com **padrões arquiteturais** aplicados:

- **API Gateway**: ponto único de entrada (`gateway/`) expondo `/api/*`.
- **Circuit Breaker**: por dependência externa, integrado ao cliente HTTP com **timeout**.
- **Bulkhead**: isolamento por serviço, limitando concorrência com semáforos.
- **IoC (Inversão de Controle)**: container simples que cria clientes HTTP e lê config via **variáveis de ambiente**.

## Componentes e portas

| Componente | Porta host | Observações |
|------------|------------|-------------|
| gateway    | 8080       | expõe `/api/*`, encaminha para serviços internos |
| user       | 5101       | Bulkhead configurável |
| inventory  | 5102       | Bulkhead configurável; suporta simulação de falhas/delay |
| payment    | 5103       | Bulkhead configurável; suporta simulação de falhas/delay |
| shipping   | 5104       | Bulkhead configurável; suporta simulação de falhas/delay |
| order      | 5105       | orquestrador com IoC + HttpClient (timeout + CB) |

## Subir os serviços

```bash
cd versao_refatorada
docker compose up --build
```

Health checks:

```bash
curl http://localhost:8080/health     # gateway
curl http://localhost:5101/health     # user
curl http://localhost:5102/health     # inventory
curl http://localhost:5103/health     # payment
curl http://localhost:5104/health     # shipping
curl http://localhost:5105/health     # order
```

## Rotas expostas no Gateway

- `GET /api/users/:id` → user
- `GET /api/stock/:sku` → inventory
- `POST /api/orders` → order (que usa user, inventory, payment, shipping)

## Fluxos de teste (via Gateway)

Buscar usuário:

```bash
curl http://localhost:8080/api/users/1
```

Consultar estoque:

```bash
curl http://localhost:8080/api/stock/SKU-001
```

Criar pedido:

```bash
curl -X POST http://localhost:8080/api/orders   -H "Content-Type: application/json"   -d '{"user_id":1,"items":[{"product_id":"SKU-001","qty":1}],"address":"Rua Exemplo, 100 - SAJ/BA"}'
```

## Circuit Breaker & simulação de falhas

Os serviços **user**, **inventory**, **payment** e **shipping** aceitam **parâmetros de simulação**:

- `?fail=1` → retorna **500** (falha simulada)
- `?delay_ms=2500` → atrasa a resposta (ex.: 2,5s)

Exemplos (direto no serviço, para forçar falhas/timeout observadas pelo **order**):

```bash
# Falha no Inventory (conta falha no breaker do cliente order→inventory)
curl "http://localhost:5102/stock/SKU-001?fail=1"

# Delay no Payment maior que o timeout (2s por padrão)
curl "http://localhost:5103/health?delay_ms=2500"
```

**Estados do breaker** (por dependência): `closed` → `open` (após N falhas) → `half_open` (após cooldown) → `closed` (se teste passa).  
Configuração via ENV (ver abaixo).

## Bulkhead (isolamento)

Cada serviço possui um semáforo interno. Ao exceder o limite, responde **503**.  
Ajuste com `BULKHEAD_LIMIT` por serviço (via docker-compose).

## Configuração por variáveis de ambiente (IoC + Cliente HTTP)

- `USER_URL`, `INVENTORY_URL`, `PAYMENT_URL`, `SHIPPING_URL`, `ORDER_URL`  
- `HTTP_TIMEOUT` (segundos, padrão **2.0**)
- `CB_THRESHOLD` (falhas para abrir, padrão **3**)
- `CB_COOLDOWN` (segundos até half-open, padrão **5**)
- `BULKHEAD_LIMIT` (por serviço, vide compose)

> O **order** injeta clientes HTTP via `common/ioc.py`, cada um com `HttpClient` (timeout + CircuitBreaker).

## Estrutura

```
versao_refatorada/
  docker-compose.yml
  README.md
  common/
    circuit_breaker.py
    bulkhead.py
    http_client.py
    ioc.py
  gateway/
    app.py
    Dockerfile
    requirements.txt
    common/...
  services/
    user/       (app.py, Dockerfile, requirements.txt, common/...)
    inventory/  (app.py, Dockerfile, requirements.txt, common/...)
    payment/    (app.py, Dockerfile, requirements.txt, common/...)
    shipping/   (app.py, Dockerfile, requirements.txt, common/...)
    order/      (app.py, Dockerfile, requirements.txt, common/...)
```

## Exemplos adicionais

Timeout curto para testar breaker:

```bash
# Ajustar timeout do gateway/ordem via ENV (compose) para 1.0s e subir novamente
# Then:
curl "http://localhost:5103/health?delay_ms=1500"
# Faça POST /api/orders e observe abertura do breaker para payment após N falhas.
```

Carga para ver Bulkhead retornando 503 (exemplo simples):

```bash
# Em um shell:
for i in $(seq 1 20); do curl -s -o /dev/null -w "%{http_code}\n"   -X POST http://localhost:5102/reserve -H "Content-Type: application/json"   -d '{"items":[{"product_id":"SKU-001","qty":1}]}' & done; wait
```

---

## Limpeza

Parar e remover containers/imagens da versão corrente:

```bash
docker compose down
```

Remover imagens (opcional):

```bash
docker image prune -f
```
