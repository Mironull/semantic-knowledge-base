# Архитектура бэкенда

## Структура модулей

```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│                   (Точка входа)                         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   app/__init__.py                       │
│              (Фабрика приложения)                       │
│                                                         │
│  create_app() → FastAPI instance                        │
│  Настройка CORS-middleware                              │
│  Регистрация роутеров                                   │
└────────┬────────────────────────────┬───────────────────┘
         │                            │
         ▼                            ▼
┌────────────────────┐    ┌───────────────────────────────┐
│  app/api/routes/   │    │     app/core/config.py        │
│                    │    │                               │
│  documents.py ─────┼────┤  Settings (pydantic-settings) │
│  health.py         │    │  - APP_NAME                   │
│                    │    │  - DB_FILE                    │
└─────────┬──────────┘    │  - CORS_ORIGINS               │
          │               └───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│           app/services/                 │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  DatabaseManager                  │  │
│  │  - insert_document()              │  │
│  │  - get_document_data()            │  │
│  │  - search_documents()             │  │
│  │  - get_all_documents()            │  │
│  │  - delete_document()              │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  DocumentParserService            │  │
│  │  parse_document(data, mime_type)  │  │
│  │                                   │  │
│  │  Парсеры (Strategy):              │  │
│  │  - TextParser  (txt, json, xml)   │  │
│  │  - PDFParser   (pdf)              │  │
│  │  - DOCXParser  (docx)             │  │
│  └───────────────────────────────────┘  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│              app/ml/                    │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  ModelRegistry (Singleton)        │  │
│  │  Управление жизненным циклом      │  │
│  │  SentenceTransformer-модели       │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  EmbeddingService                 │  │
│  │  - generate_embedding(text)       │  │
│  │  - generate_embeddings_batch()    │  │
│  │  - find_most_similar()            │  │
│  │  - compute_similarity()           │  │
│  │  - is_available()                 │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  EmbeddingDatabase                │  │
│  │  SQLite: таблица chunks           │  │
│  │  - store_chunks()                 │  │
│  │  - get_all_chunks()               │  │
│  │  - delete_chunks(doc_id)          │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  TextPreprocessor                 │  │
│  │  - Unicode NFC-нормализация       │  │
│  │  - Очистка HTML                   │  │
│  │  - Усечение (10 000 символов)     │  │
│  └───────────────────────────────────┘  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│         app/models/document.py          │
│                                         │
│  DocumentMetadata                       │
│  DocumentMetadataWithSize               │
│  DocumentSearchResult                   │
│  PreviewResponse                        │
└─────────────────────────────────────────┘
```

## Граф зависимостей

```
main.py
  └── app/__init__.py
        ├── app/api/routes/documents.py
        │     ├── app/services/database.py
        │     │     ├── app/models/document.py
        │     │     └── app/core/config.py
        │     ├── app/services/document_parser.py
        │     └── app/ml/
        │           ├── embedding_service.py
        │           │     ├── model_registry.py
        │           │     └── text_preprocessor.py
        │           └── embedding_db.py
        ├── app/api/routes/health.py
        │     └── app/core/config.py
        └── app/core/config.py
```

**Нет циклических зависимостей:**
- `core` и `models` — ни от чего не зависят
- `services` — зависят только от `models` и `core`
- `ml` — независимый модуль, не зависит от `services` или `api`
- `api` — зависит от `services`, `ml`, `models`, `core`

## Ответственность модулей

| Модуль | Ответственность | Зависит от |
|--------|----------------|------------|
| `core/config.py` | Конфигурация через pydantic-settings | — |
| `models/document.py` | Pydantic-схемы запросов/ответов | — |
| `services/database.py` | CRUD в SQLite (`docstore.db`) | models, core |
| `services/document_parser.py` | Извлечение текста из форматов | — |
| `ml/model_registry.py` | Singleton-менеджер модели | — |
| `ml/text_preprocessor.py` | Нормализация текста | — |
| `ml/embedding_service.py` | Генерация и сравнение эмбеддингов | model_registry, text_preprocessor |
| `ml/embedding_db.py` | Хранение чанков в SQLite (`embeddings.db`) | — |
| `api/routes/documents.py` | HTTP-эндпоинты документов | services, ml, models |
| `api/routes/health.py` | HTTP-эндпоинты здоровья | core |
| `app/__init__.py` | Сборка приложения, CORS, роутеры | api, core |
| `main.py` | Точка входа | app |

## Применяемые паттерны

| Паттерн | Где используется |
|---------|-----------------|
| **Factory** | `create_app()` в `app/__init__.py` |
| **Strategy** | Парсеры документов (`BaseParser` → `TextParser`, `PDFParser`, `DOCXParser`) |
| **Singleton** | `ModelRegistry` — один экземпляр модели в памяти |
| **Repository** | `DatabaseManager` — абстракция над SQLite |
| **Dependency Injection** | `Settings` через `config.py` |

## Базы данных

### docstore.db — хранилище документов

```sql
CREATE TABLE documents (
    id          TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    content_type TEXT NOT NULL,
    data        BLOB NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### embeddings.db — хранилище чанков

```sql
CREATE TABLE chunks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id       TEXT NOT NULL,
    chunk_index  INTEGER NOT NULL,
    chunk_text   TEXT,
    embedding    BLOB NOT NULL,
    embedding_dim INTEGER NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Чанковая схема позволяет индексировать большие документы по частям и находить наиболее релевантный фрагмент при поиске.
