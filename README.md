# Async Payments Processing Service
Асинхронное REST API приложение для управления пользователями, счетами и платежами.

## Стек
- Python 3.12
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- RabbitMQ (FastStream)
- Alembic
- Poetry
- Docker / Docker Compose

## Архитектура

```text
Client
  ↓
API (FastAPI)
  ↓
PostgreSQL (payments + outbox_events)
  ↓
Outbox Publisher
  ↓
RabbitMQ (payments.new)
  ↓
Consumer
  ↓
- обработка платежа (2–5 сек)
- обновление статуса
- отправка webhook
  ↓
DLQ (payments.dlq при ошибках)
```

### Возможности
- Создание платежа (POST /api/v1/payments)
- Получение информации о платеже (GET /api/v1/payments/{id})
- Idempotency-Key
- Outbox pattern (не будет race condition)
- async RabbitMQ
- Retry (3 попытки с экспоненциальной задержкой)
- Dead Letter Queue (DLQ)
- Webhook уведомления

## API
Создание платежа
```text
POST /api/v1/payments
```
Headers:
```text
X-API-Key: super-secret-test-api-key
Idempotency-Key: unique-key
```
Body:
```json
{
  "amount": "1500.50",
  "currency": "RUB",
  "description": "Test payment",
  "metadata": {
    "order_id": "123"
  },
  "webhook_url": "https://example.com/webhook"
}
```
Webhook URL можно получить по адресу https://webhook.site

Получение платежа
```text
POST /api/v1/payments/{payment_id}
```
После обработки платежа вымышленный сервис отправляет:
```json
{
  "payment_id": "uuid",
  "status": "succeeded",
  "amount": "1500.50",
  "currency": "RUB",
  "description": "Test payment",
  "metadata": {...},
  "created_at": "...",
  "processed_at": "..."
}
```

## Запуск без Docker

### 1. Установка зависимостей

```bash
poetry install
```

### 2. Создание бд и миграции
```bash
poetry run python ensure_db.py
```

### 3. Запуск API
```
poetry run uvicorn app.main:app --reload
```

## Запуск через Docker

### 1. Сборка и запуск
```bash
docker compose up --build
```

## Доступ
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- RabbitMQ UI: http://localhost:15672
  - login: guest
  - password: guest

## Автор
``` 
GitHub: https://github.com/pOsdas
```