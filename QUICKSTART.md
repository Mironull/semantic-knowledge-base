# Quick Start Guide

Get the Knowledge Base application running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 5GB free disk space
- Internet connection (first time only)

## Start the Application

```bash
# 1. Clone and navigate
cd knoweledge-base

# 2. Start services
docker compose up -d

# 3. Wait for startup (30-60 seconds)
docker compose logs -f backend
# Wait until you see: "Loaded embedding model: all-MiniLM-L6-v2"
# Press Ctrl+C to exit logs
```

## Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Try It Out

### 1. Upload a Document

1. Open http://localhost:3000
2. Expand "Управление базой знаний" (Knowledge Base Management)
3. Click "Загрузить документ" (Upload Document)
4. Select a PDF, DOCX, or TXT file
5. Click "Загрузить" (Upload)

### 2. Search with Semantic Search

Enter a query in the search box:
- "machine learning algorithms"
- "python programming"
- "data analysis"

Results show **similarity scores** as color-coded badges:
- 🟢 Green (≥70%): High relevance
- 🟠 Orange (50-69%): Moderate relevance
- ⚫ Gray (<50%): Low relevance

### 3. View Documents

1. Expand "Все документы" (All Documents)
2. Click "👁 Просмотр" (Preview) to view content
3. Click "⬇ Скачать" (Download) to download

## Stop the Application

```bash
docker compose down
```

Your data is saved in Docker volumes and will be available next time.

## Commands Cheat Sheet

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Restart
docker compose restart

# Status
docker compose ps

# Using Make (if installed)
make up        # Start
make down      # Stop
make logs      # View logs
make restart   # Restart
```

## Troubleshooting

### Backend won't start
```bash
docker compose logs backend
# Check for errors, usually port conflicts or permissions
```

### Frontend can't connect
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Need to rebuild
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## What's Running?

- **Backend**: FastAPI server with ML-powered search
- **Frontend**: React app served by Nginx
- **Databases**: SQLite (documents + embeddings)
- **ML Model**: all-MiniLM-L6-v2 (90MB, CPU-only)

## Key Features

✅ **Semantic Search**: Understands meaning, not just keywords
✅ **Similarity Scores**: See how relevant each result is
✅ **Multi-format**: PDF, DOCX, TXT, JSON, XML
✅ **Preview**: View document content in-browser
✅ **Lightweight**: 90MB model, fast on CPU
✅ **No GPU Required**: Runs on any system

## Next Steps

- See [README.md](./README.md) for full documentation
- See [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) for advanced usage
- See [ML_MODEL_INFO.md](./backend/ML_MODEL_INFO.md) for ML details

## Getting Help

```bash
# Check logs
docker compose logs -f backend
docker compose logs -f frontend

# Check container status
docker compose ps

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000/health
```

## Example API Calls

### Upload Document
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

### Search Documents
```bash
curl "http://localhost:8000/search?name=machine+learning"
```

### List All Documents
```bash
curl http://localhost:8000/documents
```

## Performance

- **Model Load**: 1-2 seconds
- **Document Upload**: ~200ms (includes embedding)
- **Search**: ~20ms (1000 documents)
- **Single Embedding**: ~8ms

## Memory Usage

- Backend: ~300MB
- Frontend: ~50MB
- Total: ~400MB RAM

Perfect for laptops and small servers!

---

Happy searching! 🚀

For detailed documentation, see [README.md](./README.md)
