# Microservices (Versão Inicial - com anti-patterns)

> **Aviso**: Esta é a *versão inicial intencionalmente frágil*, com acoplamento rígido e chamadas diretas entre serviços, **sem** API Gateway, **sem** Circuit Breaker, **sem** Bulkhead, **sem** IoC.

## Serviços (5)
- `user` (porta host 5001) — CRUD mínimo de usuários (in-memory).
- `inventory` (porta host 5002) — estoque e reserva (in-memory).
- `payment` (porta host 5003) — simulação de pagamento.
- `shipping` (porta host 5004) — criação de envio (tracking fake).
- `order` (porta host 5005) — **God/Orquestrador** que chama diretamente todos os demais.

## Como subir (Docker)
```bash
docker compose up --build
```

Aguarde os 5 serviços subirem. Endpoints de saúde:
- http://localhost:5001/health
- http://localhost:5002/health
- http://localhost:5003/health
- http://localhost:5004/health
- http://localhost:5005/health

## Fluxo de teste
1) Consulte estoque:
```bash
curl http://localhost:5002/stock/SKU-001
```

2) Crie um pedido (o serviço `order` valida usuário, reserva estoque, paga e gera envio **sincronamente**):
```bash
curl -X POST http://localhost:5005/orders \
     -H "Content-Type: application/json" \
     -d '{
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
- **Acoplamento rígido**: URLs hard-coded no `order` (sem descoberta de serviço).
- **Chamadas síncronas em cascata**: `order` → `user` → `inventory` → `payment` → `shipping`.
- **Sem timeouts/retries**: uso de `requests` sem tolerância a falhas.
- **God Service**: `order` concentra regras e orquestra tudo.
- **Sem idempotência/rollback**: reserva de estoque sem compensação.

## Estrutura do repositório
```
/versao_inicial/
  docker-compose.yml
  README.md
  services/
    user/
      app.py
      Dockerfile
      requirements.txt
    inventory/
      app.py
      Dockerfile
      requirements.txt
    payment/
      app.py
      Dockerfile
      requirements.txt
    shipping/
      app.py
      Dockerfile
      requirements.txt
    order/
      app.py
      Dockerfile
      requirements.txt
```

## Publicação no GitHub
1. Crie um repositório (público).
2. Na raiz do repositório, coloque esta pasta **/versao_inicial/** exatamente com esse nome.
3. Faça o push:
   ```bash
   git add versao_inicial
   git commit -m "Etapa 1: versão inicial (anti-patterns)"
   git branch -M main
   git remote add origin <URL_DO_SEU_REPO>
   git push -u origin main
   ```
