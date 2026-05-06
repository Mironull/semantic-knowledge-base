# База знаний — Семантический поиск документов

Полнофункциональное приложение для хранения документов и семантического поиска на базе машинного обучения. Загружайте документы и ищите по смыслу запроса на русском, английском и ещё 50+ языках.

## Стек технологий

**Бэкенд**: Python 3.12, FastAPI, SQLite, sentence-transformers, PyTorch (CPU)  
**Фронтенд**: React 19, Create React App, Nginx (в Docker)  
**Инфраструктура**: Docker, Docker Compose

## Быстрый старт с Docker

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- 5 ГБ свободного места на диске

### Запуск

```bash
# Клонировать репозиторий
git clone <url-репозитория>
cd knoweledge-base

# Запустить все сервисы
docker compose up -d

# Или через Make
make up
```

Доступ к приложению:
- **Фронтенд**: http://localhost:3000
- **Бэкенд API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs

### Остановка

```bash
docker compose down
# или
make down
```

## Локальная разработка

### Бэкенд

```bash
cd backend

# Создать и активировать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
uvicorn main:app --reload
```

Бэкенд работает на: http://localhost:8000

### Фронтенд

```bash
cd frontend

npm install
npm start
```

Фронтенд работает на: http://localhost:3000

## Архитектура

### Бэкенд (`/backend`)

Модульная архитектура с чётким разделением слоёв:

```
backend/
├── app/
│   ├── __init__.py          # Фабрика приложения (create_app)
│   ├── api/routes/          # HTTP-эндпоинты
│   │   ├── documents.py     # CRUD документов + поиск
│   │   └── health.py        # Проверка работоспособности
│   ├── services/            # Бизнес-логика
│   │   ├── database.py      # DatabaseManager (SQLite)
│   │   └── document_parser.py  # Парсинг форматов (Strategy)
│   ├── ml/                  # Машинное обучение
│   │   ├── model_registry.py    # Singleton-менеджер модели
│   │   ├── embedding_service.py # Генерация эмбеддингов
│   │   ├── embedding_db.py      # SQLite для чанков
│   │   └── text_preprocessor.py # Очистка текста
│   ├── models/              # Pydantic-модели
│   │   └── document.py
│   └── core/                # Конфигурация
│       └── config.py
├── main.py                  # Точка входа
├── requirements.txt
└── Dockerfile
```

### Фронтенд (`/frontend`)

```
frontend/
├── src/
│   ├── App.js               # Главный компонент
│   └── index.js
├── public/
├── package.json
├── Dockerfile
└── nginx.conf               # Конфигурация Nginx для production
```

## API-эндпоинты

### Документы

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/upload` | Загрузить документ (автогенерация эмбеддингов) |
| `GET` | `/documents` | Список всех документов с метаданными |
| `GET` | `/search?name={запрос}` | Семантический поиск |
| `GET` | `/preview/{doc_id}` | Просмотр текста документа |
| `GET` | `/download/{doc_id}` | Скачать документ |
| `DELETE` | `/documents/{doc_id}` | Удалить документ и его эмбеддинги |

### Служебные

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/` | Приветственное сообщение |
| `GET` | `/health` | Проверка работоспособности |

Интерактивная документация: http://localhost:8000/docs

## Машинное обучение

Приложение использует **sentence-transformers** для семантического поиска.

### Текущая модель: `paraphrase-multilingual-mpnet-base-v2`

| Параметр | Значение |
|----------|----------|
| Размерность эмбеддинга | 768 |
| Размер модели | ~1,5 ГБ |
| Поддерживаемые языки | 50+, включая русский |
| Устройство | CPU |

### Конвейер обработки

**При загрузке документа:**
1. Документ сохраняется в `docstore.db`
2. Текст извлекается через `DocumentParserService`
3. Текст разбивается на чанки
4. Каждый чанк встраивается в вектор
5. Чанки сохраняются в `embeddings.db` (таблица `chunks`)

**При поиске:**
1. Запрос преобразуется в вектор
2. Из базы извлекаются все чанки
3. Вычисляется косинусное сходство
4. Для каждого документа выбирается лучший чанк
5. Возвращается топ-N документов с оценкой похожести

**Деградация:** если ML недоступен, поиск переключается на поиск по имени файла.

## Базы данных

| База | Файл | Содержимое |
|------|------|------------|
| Документы | `docstore.db` | id, filename, content_type, data (BLOB), upload_date |
| Эмбеддинги | `embeddings.db` | doc_id, chunk_index, chunk_text, embedding (BLOB), embedding_dim |

В Docker данные хранятся в томах и сохраняются между перезапусками.

## Поддерживаемые форматы

PDF, DOCX, TXT, JSON, XML, HTML, CSV

## Конфигурация

### Бэкенд (`backend/.env`)

```bash
APP_NAME=Knowledge Base API
DB_FILE=/app/data/docstore.db
CORS_ORIGINS=http://localhost:3000,http://localhost:80
```

### Фронтенд (`frontend/.env`)

```bash
REACT_APP_API_URL=http://localhost:8000
```

## Docker-команды

```bash
# Сборка образов
make build          # или: docker compose build

# Запуск
make up             # или: docker compose up -d

# Логи
make logs           # или: docker compose logs -f

# Перезапуск
make restart        # или: docker compose restart

# Остановка
make down           # или: docker compose down

# Полная очистка с томами
make clean          # или: docker compose down -v
```

## Примеры запросов к API

```bash
# Загрузить документ
curl -X POST http://localhost:8000/upload -F "file=@document.pdf"

# Поиск на русском
curl "http://localhost:8000/search?name=машинное+обучение"

# Поиск на английском
curl "http://localhost:8000/search?name=machine+learning"

# Список всех документов
curl http://localhost:8000/documents

# Удалить документ
curl -X DELETE http://localhost:8000/documents/{doc_id}
```

## Производительность

| Операция | Время (CPU) |
|----------|-------------|
| Загрузка модели | 1–2 с |
| Генерация одного эмбеддинга | ~8 мс |
| Пакетная обработка (32 текста) | ~150 мс |
| Поиск (1000 документов) | ~20 мс |
| Загрузка документа с эмбеддингом | ~200 мс |

**Потребление памяти**: бэкенд ~300 МБ, фронтенд ~50 МБ, модель ~100 МБ.

## Устранение неполадок

**Бэкенд не запускается:**
```bash
docker compose logs backend
# Проверить занятость порта 8000, права на файлы
```

**Фронтенд не подключается к бэкенду:**
```bash
curl http://localhost:8000/health
# Ожидается: {"status": "healthy"}
# Проверить REACT_APP_API_URL и CORS_ORIGINS
```

**ML не работает:**
```bash
# Проверить наличие 5 ГБ свободного места
# Проверить логи при первом запуске — загрузка модели занимает время
docker compose logs backend | grep -i model
```

**Сброс данных:**
```bash
docker compose down -v && docker compose up -d
```

## Документация

- [Быстрый старт](./QUICKSTART.md)
- [История изменений](./CHANGELOG.md)
- [Архитектура бэкенда](./backend/ARCHITECTURE.md)
- [ML-интеграция](./backend/ML_INTEGRATION.md)
- [Информация о модели](./backend/ML_MODEL_INFO.md)
- [Swagger UI](http://localhost:8000/docs) (при запущенном сервере)

## Лицензия

MIT License
