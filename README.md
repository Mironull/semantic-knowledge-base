# Knowledge Base Search Application

Full-stack knowledge base with semantic search powered by machine learning. Upload documents and search using natural language queries in multiple languages including Russian.

## Features

- 📄 **Multi-format Support**: PDF, DOCX, TXT, JSON, XML
- 🔍 **Semantic Search**: ML-powered search that understands meaning
- 🌐 **Multilingual**: Supports Russian, English, and 50+ languages
- 🤖 **Automatic Embeddings**: Generated on upload, transparent to users
- 👁️ **Document Preview**: View content before downloading
- 📦 **Dual Databases**: Separate storage for documents and embeddings
- 🎯 **Modern UI**: React frontend with dark mode
- 🚀 **FastAPI Backend**: High-performance REST API
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## Quick Start with Docker (Recommended)

### Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

### Start the Application

```bash
# Clone the repository
git clone <repository-url>
cd knoweledge-base

# Start all services
docker compose up -d

# Or use Make
make up
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Stop the Application

```bash
docker compose down

# Or use Make
make down
```

For detailed Docker documentation, see [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)

## Local Development Setup

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend runs at: http://localhost:3000

## Architecture

### Backend (`/backend`)

- **Framework**: FastAPI + Uvicorn
- **Language**: Python 3.11
- **Databases**: SQLite (documents + embeddings)
- **ML**: sentence-transformers (paraphrase-multilingual-mpnet-base-v2)
- **Features**:
  - RESTful API with automatic OpenAPI docs
  - Document parsing for multiple formats
  - Semantic search with embeddings
  - Multilingual support

**Structure**:
```
backend/
├── app/
│   ├── api/routes/      # HTTP endpoints
│   ├── services/        # Business logic
│   ├── ml/              # Machine learning
│   ├── models/          # Data models
│   └── core/            # Configuration
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── Dockerfile          # Docker build
```

### Frontend (`/frontend`)

- **Framework**: React 19
- **Build Tool**: Create React App
- **Server**: Nginx (in Docker)
- **Features**:
  - Modern responsive UI
  - Dark mode support
  - Voice search (Russian)
  - Document preview modal
  - Search history

**Structure**:
```
frontend/
├── src/
│   ├── App.js           # Main component
│   └── index.js         # Entry point
├── public/              # Static assets
├── package.json         # Dependencies
├── Dockerfile          # Docker build
└── nginx.conf          # Production server config
```

## API Endpoints

### Documents

- `POST /upload` - Upload document with auto-embedding generation
- `GET /download/{doc_id}` - Download document
- `GET /search?name={query}` - Semantic search
- `GET /documents` - List all documents
- `GET /preview/{doc_id}` - Preview document text

### Health

- `GET /` - API health check

Full API documentation: http://localhost:8000/docs

## Machine Learning

The application uses **sentence-transformers** for semantic search:

- **Model**: `paraphrase-multilingual-mpnet-base-v2`
- **Dimensions**: 768
- **Languages**: 50+ including Russian and English
- **Search Method**: Cosine similarity

### How It Works

1. **Upload**: Document → Text extraction → Embedding generation → Storage
2. **Search**: Query → Embedding generation → Similarity computation → Ranked results
3. **Fallback**: If ML unavailable, falls back to filename search

See [ML_INTEGRATION.md](./backend/ML_INTEGRATION.md) for details.

## Configuration

### Backend Configuration

Create `backend/.env`:
```bash
APP_NAME=Knowledge Base API
DB_FILE=/app/data/docstore.db
CORS_ORIGINS=http://localhost:3000,http://localhost:80
```

### Frontend Configuration

Create `frontend/.env`:
```bash
REACT_APP_API_URL=http://localhost:8000
```

## Docker Deployment

### Using Makefile

```bash
# Build images
make build

# Start services
make up

# View logs
make logs

# Restart services
make restart

# Stop services
make down

# Full cleanup
make clean

# Complete rebuild
make rebuild
```

### Manual Docker Commands

```bash
# Build
docker compose build

# Start
docker compose up -d

# Logs
docker compose logs -f

# Stop
docker compose down
```

### Data Persistence

Data is persisted in Docker volumes:
- `backend-data`: Stores SQLite databases
- `model-cache`: Caches ML models (~1.5GB)

Volumes survive container restarts. To backup:
```bash
make backup
```

## Common Tasks

### Upload a Document

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

### Search Documents

```bash
# Semantic search
curl "http://localhost:8000/search?name=machine+learning"

# Russian query
curl "http://localhost:8000/search?name=машинное+обучение"
```

### List All Documents

```bash
curl http://localhost:8000/documents
```

### Download Document

```bash
curl -O http://localhost:8000/download/{doc_id}
```

## Development

### Backend Testing

```bash
cd backend
pytest
```

### Frontend Testing

```bash
cd frontend
npm test
```

### Code Formatting

Backend (Python):
```bash
cd backend
black app/
isort app/
```

Frontend (JavaScript):
```bash
cd frontend
npm run format
```

## Troubleshooting

### Backend won't start

1. Check if port 8000 is available
2. Verify Python dependencies installed
3. Check logs: `docker compose logs backend`

### Frontend can't connect to backend

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in backend configuration
3. Verify `REACT_APP_API_URL` in frontend `.env`

### ML features not working

1. Check if sentence-transformers installed
2. Verify disk space (~1.5GB for model)
3. Check backend logs for model loading errors
4. Wait for first-time model download

### Database issues

1. Check volume permissions
2. Verify database files exist in volume
3. Try resetting: `docker compose down -v && docker compose up -d`

## Performance

### Backend

- **Single text embedding**: ~10-50ms (CPU)
- **Batch embeddings**: ~200-500ms for 32 texts (CPU)
- **Search (1000 docs)**: ~50ms
- **Model loading**: ~2-5s (first time: downloads ~1.5GB)

### Frontend

- **Initial load**: ~500ms
- **Search response**: <100ms (network + backend)
- **Document preview**: <200ms

### Optimization

- Use GPU for 5-10x faster embeddings
- Enable caching (already configured)
- Use CDN for static assets
- Scale backend horizontally

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Documentation

- [Docker Deployment Guide](./DOCKER_DEPLOYMENT.md)
- [ML Integration Details](./backend/ML_INTEGRATION.md)
- [Backend Architecture](./backend/ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## Tech Stack

**Backend**:
- FastAPI
- SQLite
- sentence-transformers
- PyTorch
- NumPy
- PyPDF2, python-docx

**Frontend**:
- React 19
- Create React App
- Nginx (production)

**Infrastructure**:
- Docker & Docker Compose
- Python 3.11
- Node 18

## License

MIT License

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API docs at `/docs`

## Roadmap

- [ ] User authentication
- [ ] Document folders/tags
- [ ] Advanced filters
- [ ] Export search results
- [ ] Batch document upload
- [ ] Admin dashboard
- [ ] Vector database integration (FAISS)
- [ ] Multi-tenant support
