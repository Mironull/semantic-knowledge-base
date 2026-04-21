# Document Store Backend

FastAPI backend for document storage with search and preview capabilities.

## Features

- 📄 Multiple file format support: PDF, DOCX, TXT, JSON, XML
- 🔍 Full-text search by filename
- 👁️ Document preview for text-based formats
- 📦 SQLite database for storage
- 🎯 Modular architecture with independent components
- 🔒 Type-safe with full type annotations

### Working with Virtual Environment

```bash
# init venv
python -m venv ./venv
# activate venv
source ./venv/bin/activate
```

```bash
# deactive venv
deactivate
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

### Running the server

```bash
# Option 1: Using uvicorn directly
uvicorn main:app --reload

# Option 2: Using Python
python main.py
```

**Endpoints:**
- API: http://127.0.0.1:8000
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- OpenAPI Spec: http://127.0.0.1:8000/openapi.json
- Health Check: http://127.0.0.1:8000/health

## Architecture

The backend uses a modular architecture with independent components:

```
app/
├── api/routes/      # HTTP endpoints
├── services/        # Business logic
├── models/          # Data models
└── core/            # Configuration
```

See `app/README.md` for detailed architecture documentation.

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Configuration options:
- `APP_NAME` - Application name
- `DB_FILE` - SQLite database path
- `CORS_ORIGINS` - Allowed CORS origins