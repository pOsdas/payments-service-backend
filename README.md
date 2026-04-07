# Test Backend (FastAPI + PostgreSQL)
Асинхронное REST API приложение для управления пользователями, счетами и платежами.

## Стек
- Python 3.12
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Alembic
- Poetry
- Docker / Docker Compose

## Запуск без Docker

### 1. Установка зависимостей

```bash
poetry install
```

### 2. Создание базы данных
```bash
poetry run python ensure_db.py
```

### 3. Применение миграций
```bash
poetry run alembic upgrade head
```

### 4. Запуск приложения
```
poetry run uvicorn app.main:app --reload
```

Приложение будет доступно по адресу:

- http://localhost:8000
- Swagger: http://localhost:8000/docs

## Запуск через Docker

### 1. Сборка и запуск
```bash
docker compose up --build
```

### 2. Приложение будет доступно:

- http://localhost:8000
- Swagger: http://localhost:8000/docs

## Учетные данные по умолчанию
### Admin:
- email: admin@example.com
- password: admin12345
- hashed_password: $2b$12$E8yWZJ3/1R4v91l/xgZObOm68Uk4KXVaPDLbxljSFKTYE6gND.96S
### User:
- email: user@example.com
- password: user12345
- hashed_password: $2b$12$z1Dm78Di/1kOPfM6titrCupzEZRH7NQlZ.z747HxwYAxjlgRtijBq

## 💰 Webhook платежа
Endpoint:
`POST /api/v1/payments/webhook` \
Пример запроса:
```json
{
  "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
  "user_id": 2,
  "account_id": 1,
  "amount": 100,
  "signature": "48c42941e65822114a136ec0bee75b12644347407a47c897989a8329d39bb62e"
}
```

## \> Тестовая подпись
temp_signature: `48c42941e65822114a136ec0bee75b12644347407a47c897989a8329d39bb62e`

## Автор
``` 
GitHub: https://github.com/pOsdas
```