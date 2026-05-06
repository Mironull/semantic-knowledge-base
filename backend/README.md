# Бэкенд — Document Store API

FastAPI-бэкенд для хранения документов, семантического поиска и предпросмотра. Python 3.12, SQLite, sentence-transformers.

## Функции

- Загрузка и хранение документов (PDF, DOCX, TXT, JSON, XML, HTML, CSV)
- Семантический поиск на базе ML-эмбеддингов
- Предпросмотр текстовых документов
- Автоматическая генерация эмбеддингов при загрузке
- Деградация: при недоступности ML — поиск по имени файла
- Модульная архитектура с полным разделением слоёв

## Запуск

### Виртуальное окружение

```bash
# Создать
python -m venv ./venv

# Активировать
source ./venv/bin/activate      # Linux / macOS
# venv\Scripts\activate          # Windows

# Деактивировать
deactivate
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск сервера

```bash
# С горячей перезагрузкой (для разработки)
uvicorn main:app --reload

# Без горячей перезагрузки
uvicorn main:app
```

## Адреса

| URL | Описание |
|-----|----------|
| http://127.0.0.1:8000 | API |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/openapi.json | OpenAPI-спецификация |
| http://127.0.0.1:8000/health | Проверка работоспособности |

## API-эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/upload` | Загрузить документ + сгенерировать эмбеддинги |
| `GET` | `/documents` | Список документов с метаданными и размером |
| `GET` | `/search?name={запрос}` | Семантический поиск |
| `GET` | `/preview/{doc_id}` | Предпросмотр текста документа |
| `GET` | `/download/{doc_id}` | Скачать документ |
| `DELETE` | `/documents/{doc_id}` | Удалить документ и его эмбеддинги |
| `GET` | `/` | Приветствие |
| `GET` | `/health` | Статус сервиса |

## Структура проекта

```
backend/
├── app/
│   ├── __init__.py              # Фабрика приложения create_app()
│   ├── api/
│   │   └── routes/
│   │       ├── documents.py     # Эндпоинты документов
│   │       └── health.py        # Эндпоинты здоровья
│   ├── services/
│   │   ├── database.py          # DatabaseManager (SQLite)
│   │   └── document_parser.py   # Парсеры форматов (Strategy)
│   ├── ml/
│   │   ├── model_registry.py    # Singleton-менеджер модели
│   │   ├── embedding_service.py # Генерация эмбеддингов
│   │   ├── embedding_db.py      # Хранилище чанков
│   │   └── text_preprocessor.py # Нормализация текста
│   ├── models/
│   │   └── document.py          # Pydantic-модели
│   └── core/
│       └── config.py            # Настройки (pydantic-settings)
├── main.py                      # Точка входа
├── requirements.txt
├── Dockerfile
├── docstore.db                  # SQLite: документы
└── embeddings.db                # SQLite: эмбеддинги чанков
```

Подробная архитектура: [ARCHITECTURE.md](./ARCHITECTURE.md)

## Конфигурация

Скопировать `.env.example` в `.env` и настроить:

```bash
APP_NAME=Knowledge Base API
DB_FILE=docstore.db              # Путь к базе документов
CORS_ORIGINS=http://localhost:3000
```

## Зависимости

Ключевые пакеты из `requirements.txt`:

| Пакет | Версия | Назначение |
|-------|--------|------------|
| fastapi | 0.135.3 | Web-фреймворк |
| uvicorn | 0.44.0 | ASGI-сервер |
| pydantic | 2.12.5 | Валидация данных |
| pydantic-settings | 2.1.0 | Конфигурация |
| sentence-transformers | 3.1.1 | ML-эмбеддинги |
| torch | 2.2.2+cpu | CPU-версия PyTorch |
| numpy | 1.26.4 | Работа с векторами |
| PyPDF2 | 3.0.1 | Парсинг PDF |
| python-docx | 1.1.0 | Парсинг DOCX |
