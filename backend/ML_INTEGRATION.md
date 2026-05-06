# ML-интеграция — Семантический поиск

## Обзор

Модуль машинного обучения встроен прозрачно в процессы загрузки и поиска документов. Использует sentence-transformers для генерации векторных эмбеддингов и косинусного сравнения.

## Структура модуля

```
backend/app/ml/
├── __init__.py              # Экспорты модуля
├── model_registry.py        # Singleton-менеджер модели
├── embedding_service.py     # Высокоуровневый интерфейс
├── embedding_db.py          # SQLite-хранилище чанков
└── text_preprocessor.py     # Очистка и нормализация текста
```

## Компоненты

### ModelRegistry (`model_registry.py`)

Управляет жизненным циклом `SentenceTransformer`-модели по паттерну Singleton: модель загружается один раз и переиспользуется всеми запросами.

- Автоматическая загрузка и прогрев модели при старте
- Управление устройством (CPU / CUDA)
- Хранение метаданных модели (размерность, количество параметров)

### EmbeddingService (`embedding_service.py`)

Высокоуровневый интерфейс для работы с эмбеддингами.

| Метод | Описание |
|-------|----------|
| `generate_embedding(text)` | Генерация вектора для одного текста |
| `generate_embeddings_batch(texts)` | Пакетная генерация |
| `find_most_similar(query_emb, chunks)` | Поиск похожих чанков |
| `compute_similarity(emb1, emb2)` | Косинусное сходство двух векторов |
| `is_available()` | Проверка доступности ML |

**Предобработка текста** (через `TextPreprocessor`):
- NFC-нормализация Unicode
- Удаление HTML-тегов
- Удаление URL и email
- Коллапс пробелов
- Усечение до 10 000 символов

### EmbeddingDatabase (`embedding_db.py`)

Хранилище чанков в SQLite (`embeddings.db`).

```sql
CREATE TABLE chunks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id        TEXT NOT NULL,
    chunk_index   INTEGER NOT NULL,
    chunk_text    TEXT,
    embedding     BLOB NOT NULL,       -- numpy-массив, сериализованный через numpy.tobytes()
    embedding_dim INTEGER NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Метод | Описание |
|-------|----------|
| `store_chunks(doc_id, chunks, embeddings)` | Сохранить чанки документа |
| `get_all_chunks()` | Получить все чанки для поиска |
| `delete_chunks(doc_id)` | Удалить все чанки документа |
| `get_chunk_count()` | Количество сохранённых чанков |

## Конвейер данных

### Загрузка документа (`POST /upload`)

```
Входной файл (PDF / DOCX / TXT / ...)
        │
        ▼
DatabaseManager.insert_document()
  → Сохраняется в docstore.db (BLOB + метаданные)
        │
        ▼
DocumentParserService.parse_document()
  → Извлечение текста согласно MIME-типу
        │
        ▼
TextPreprocessor
  → Unicode NFC, очистка HTML, усечение до 10 000 символов
        │
        ▼
Разбивка текста на чанки (chunk splitting)
        │
        ▼
EmbeddingService.generate_embeddings_batch(chunks)
  → Пакетная генерация 384-мерных векторов
        │
        ▼
EmbeddingDatabase.store_chunks(doc_id, chunks, embeddings)
  → Запись в embeddings.db
```

Весь процесс прозрачен для API-клиента: ответ возвращается сразу после сохранения документа.

### Семантический поиск (`GET /search?name=...`)

```
Текст запроса
        │
        ▼
EmbeddingService.generate_embedding(query)
  → Вектор запроса (384 измерения)
        │
        ▼
EmbeddingDatabase.get_all_chunks()
  → Все сохранённые чанки с векторами
        │
        ▼
Косинусное сходство: query_emb · chunk_emb
  → Оценка для каждого чанка
        │
        ▼
Агрегация: выбор лучшего чанка по каждому doc_id
        │
        ▼
Сортировка по оценке, возврат топ-N документов
  → DocumentSearchResult { similarity_score, chunk_text, chunk_index, ... }
        │
        ▼ (если ML недоступен)
DatabaseManager.search_documents(query)
  → Поиск по имени файла (fallback)
```

## Деградация при недоступности ML

| Ситуация | Поведение |
|----------|-----------|
| `sentence-transformers` не установлен | Загрузка работает, эмбеддинги не генерируются, поиск по имени файла |
| Модель не загружается | `is_available()` → False, fallback-поиск |
| Ошибка генерации эмбеддинга | Логируется, документ всё равно сохраняется |

## Конфигурация модели

По умолчанию используется `paraphrase-multilingual-mpnet-base-v2`. Для смены модели отредактировать инициализацию `EmbeddingService` в `app/api/routes/documents.py`:

```python
embedding_service = EmbeddingService(
    model_name='paraphrase-multilingual-MiniLM-L12-v2',  # 384 dims, 420 МБ, 50+ языков, быстрее
    device='cpu',
    enable_preprocessing=True
)
```

После смены модели необходимо очистить кэш и пересгенерировать эмбеддинги:

```bash
# Очистить кэш модели
docker volume rm <project>_model-cache

# Пересобрать и перезапустить
docker compose build --no-cache backend
docker compose up -d
```

## Производительность

| Операция | Время (CPU, paraphrase-multilingual-mpnet-base-v2) |
|----------|--------------------------------------------------|
| Загрузка модели | 2–5 с (первый раз — загрузка ~1,5 ГБ) |
| Один эмбеддинг | ~10–50 мс |
| Пакет 32 текста | ~200–500 мс |
| Поиск по 1 000 документов | ~50 мс |
| Поиск по 10 000 документов | ~500 мс |
| Загрузка документа с эмбеддингом | ~300–500 мс |

**Память:**
- Модель в RAM: ~1,5 ГБ
- Один эмбеддинг: 768 × 4 байта = 3 КБ
- 10 000 чанков: ~30 МБ в `embeddings.db`

Поиск масштабируется линейно. Для баз >100 тыс. документов рассмотрите FAISS или Milvus.

## Примеры запросов

```bash
# Русский
curl "http://localhost:8000/search?name=машинное+обучение"
curl "http://localhost:8000/search?name=нейронные+сети"

# Английский
curl "http://localhost:8000/search?name=neural+networks"
curl "http://localhost:8000/search?name=deep+learning"
```

Ответ содержит:
```json
[
  {
    "id": "uuid",
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "upload_date": "2026-05-06T12:00:00",
    "size": 204800,
    "similarity_score": 0.87,
    "chunk_text": "...релевантный фрагмент...",
    "chunk_index": 2
  }
]
```

## Мониторинг

Логи ML-сервиса при старте:
```
Loading model 'paraphrase-multilingual-mpnet-base-v2' on device 'cpu'...
Model loaded in 3.2s | dim=768 | params=420M | max_seq=512
Running warm-up inference...
Warm-up complete.
```

Проверка доступности:
```python
if embedding_service.is_available():
    dim = embedding_service.get_embedding_dimension()  # 768
    count = embedding_db.get_chunk_count()
```
