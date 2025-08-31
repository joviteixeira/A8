# Microservices — Versão Refatorada (/versao_refatorada)

Esta versão aplica **padrões arquiteturais** sobre a versão inicial:
- **API Gateway** (`gateway/`): ponto único de entrada `/api/*`.
- **Circuit Breaker**: por serviço externo (User/Inventory/Payment/Shipping) usando `common/circuit_breaker.py` integrado ao `HttpClient`.
- **Bulkhead**: limite de concorrência por serviço (semáforo), retornando **503** quando o compartimento está cheio.
- **IoC (Inversão de Controle)**: `common/ioc.py` constrói clientes HTTP com configs via **ENV**.

## Subindo com Docker
```bash
docker compose up --build
```

Serviços (host:porta):
- gateway: **8080**
- user: 5101 → container 5000
- inventory: 5102 → container 5000
- payment: 5103 → container 5000
- shipping: 5104 → container 5000
- order: 5105 → container 5000

## Testes
Health:
```bash
curl http://localhost:8080/health
curl http://localhost:5101/health
curl http://localhost:5102/health
curl http://localhost:5103/health
curl http://localhost:5104/health
curl http://localhost:5105/health
```

### Via Gateway
Buscar usuário:
```bash
curl http://localhost:8080/api/users/1
```

Criar pedido (passa pelos breakers dos clientes do `order`):
```bash
curl -X POST http://localhost:8080/api/orders \      -H "Content-Type: application/json" \      -d '{{"user_id":1,"items":[{{"product_id":"SKU-001","qty":1}}], "address":"Rua Exemplo, 100 - SAJ/BA"}}'
```

Consultar estoque via Gateway:
```bash
curl http://localhost:8080/api/stock/SKU-001
```

### Simular falhas/timeouts (para acionar o Circuit Breaker)
Nos serviços **user**, **inventory**, **payment** e **shipping** há suporte a:
- `?fail=1` → retorna **500** (falha simulada)
- `?delay_ms=2000` → atrasa a resposta (pode causar timeout no cliente)

Exemplos:
```bash
# Simular falha do estoque
curl "http://localhost:5102/stock/SKU-001?fail=1"

# Simular delay no pagamento (2.5s). Com timeout de 2.0s, breaker contará falha.
curl "http://localhost:5103/health?delay_ms=2500"
```

### Bulkhead (Isolamento por compartimento)
Cada serviço tem `BULKHEAD_LIMIT` configurável por ENV. Quando excedido, a rota retorna **503**:
```bash
# Ex.: aumentar pressão com várias chamadas simultâneas para /reserve
```

### IoC / Config
Variáveis de ambiente (exemplos):
- `USER_URL`, `INVENTORY_URL`, `PAYMENT_URL`, `SHIPPING_URL`, `ORDER_URL`
- `HTTP_TIMEOUT` (padrão 2.0s)
- `CB_THRESHOLD` (padrão 3 falhas)
- `CB_COOLDOWN` (padrão 5s)
- `BULKHEAD_LIMIT` por serviço

### Estrutura
```
/versao_refatorada/
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
    user/ (app.py, Dockerfile, requirements.txt, common/...)
    inventory/ (...)
    payment/ (...)
    shipping/ (...)
    order/ (...)
```

## Observações
- O **API Gateway** centraliza a borda HTTP pública e mantém os serviços internos sem exposição externa.
- O **Circuit Breaker** troca para estado **OPEN** após N falhas; em **HALF_OPEN** testa chamadas após cooldown.
- O **Bulkhead** usa semáforos simples para limitar concorrência por serviço/rota.
- O **IoC** desacopla configuração de URLs/tempos e instancia clientes sob demanda.
