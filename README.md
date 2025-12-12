# Demo FastAPI Service

Демонстрационный backend на FastAPI с healthcheck endpoint, Docker поддержкой и CI/CD.

## Локальный запуск

### С Poetry

```
poetry install
poetry run uvicorn app.main:app --reload
```

### С Docker Compose

```
docker-compose up --build
```

Приложение доступно на http://localhost:8000

## Endpoints

- `GET /healthcheck` - Проверка работоспособности
- `GET /docs` - Swagger UI документация
- `GET /openapi.json` - OpenAPI спецификация

## Тестирование

```
poetry run pytest tests/ -v
```

## CI/CD

GitHub Actions автоматически:
- Проверяет качество кода
- Запускает unit тесты
- Собирает Docker образ
- Выполняет интеграционные тесты
- Генерирует OpenAPI спецификацию
- Публикует документацию на GitHub Pages

## GitHub Pages

API документация доступна по адресу: https://project11b-backend-svobodnaya.onrender.com/docs