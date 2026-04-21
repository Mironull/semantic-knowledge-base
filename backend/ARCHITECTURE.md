# Backend Architecture

## Module Structure

```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│                   (Entry Point)                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   app/__init__.py                       │
│              (Application Factory)                      │
│                                                         │
│  - create_app() → FastAPI instance                     │
│  - Configure middleware (CORS)                          │
│  - Register routers                                     │
└─────────┬────────────────────────────┬──────────────────┘
          │                            │
          ▼                            ▼
┌─────────────────────┐    ┌────────────────────────────┐
│   app/api/routes/   │    │     app/core/config.py     │
│                     │    │                            │
│  - documents.py     │◄───┤  Settings (pydantic)       │
│  - health.py        │    │  - APP_NAME                │
│                     │    │  - DB_FILE                 │
└──────────┬──────────┘    │  - CORS_ORIGINS            │
           │               └────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│       app/services/                 │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  DatabaseManager             │  │
│  │  - insert_document()         │  │
│  │  - get_document_data()       │  │
│  │  - search_documents()        │  │
│  │  - get_all_documents()       │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  DocumentParserService       │  │
│  │  - parse_document()          │  │
│  │                              │  │
│  │  Parsers:                    │  │
│  │  - TextParser                │  │
│  │  - PDFParser                 │  │
│  │  - DOCXParser                │  │
│  └──────────────────────────────┘  │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       app/models/document.py        │
│                                     │
│  - DocumentMetadata                │
│  - DocumentMetadataWithSize        │
│  - PreviewResponse                 │
└─────────────────────────────────────┘
```

## Dependency Flow

```
┌──────────┐
│  main.py │
└────┬─────┘
     │
     ├─► app/__init__.py
     │        │
     │        ├─► app/api/routes/documents.py
     │        │        │
     │        │        ├─► app/services/database.py
     │        │        │        │
     │        │        │        └─► app/models/document.py
     │        │        │        └─► app/core/config.py
     │        │        │
     │        │        └─► app/services/document_parser.py
     │        │
     │        ├─► app/api/routes/health.py
     │        │        │
     │        │        └─► app/core/config.py
     │        │
     │        └─► app/core/config.py
```

## Independence

### No Circular Dependencies
- `core` has no dependencies on other modules
- `models` has no dependencies on other modules
- `services` depends only on `models` and `core`
- `api` depends on `services`, `models`, and `core`
- `app/__init__` depends on `api`, `core`

## Module Responsibilities

| Module | Responsibility | Depends On |
|--------|---------------|------------|
| `core/config.py` | Configuration management | None |
| `models/document.py` | Data structures | None |
| `services/database.py` | Data persistence | models, core |
| `services/document_parser.py` | Document parsing | None |
| `api/routes/documents.py` | HTTP endpoints for documents | services, models |
| `api/routes/health.py` | HTTP endpoints for health | core |
| `app/__init__.py` | Application assembly | api, core |
| `main.py` | Application entry | app |
