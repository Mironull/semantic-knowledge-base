# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Docker support with multi-stage builds
- docker-compose.yml for easy deployment
- Makefile for common Docker operations
- CPU-only PyTorch installation (no CUDA dependencies)
- Similarity scores displayed in frontend search results
- Color-coded similarity badges (green/orange/gray)
- ML model configuration documentation
- Comprehensive Docker deployment guide
- Quick start guide for Docker

### Changed
- Switched ML model from `paraphrase-multilingual-mpnet-base-v2` to `all-MiniLM-L6-v2`
  - 16x smaller download (90MB vs 1.5GB)
  - 3-5x faster inference
  - Better suited for CPU-only environments
- Updated search API to return similarity scores
- Modified frontend to display similarity percentages
- Optimized Docker images for size and build speed

### Improved
- Backend Dockerfile optimized for caching
- Frontend uses nginx for production serving
- Added health checks for containers
- Persistent volumes for data and model cache
- Environment variable configuration
- API documentation with similarity score examples

### Fixed
- Removed CUDA dependencies for cleaner CPU-only deployment
- Fixed frontend API URL configuration with environment variables

## [0.1.0] - Initial Release

### Added
- FastAPI backend with document management
- React frontend with search interface
- SQLite databases (documents + embeddings)
- Machine learning semantic search
- Document upload and preview
- Multi-format support (PDF, DOCX, TXT, JSON, XML)
- Multilingual text preprocessing
- Automatic embedding generation
- Cosine similarity search
- Dark mode UI
- Voice search (Russian)
- Search history
- Document list view

### Backend Features
- RESTful API with OpenAPI docs
- Application factory pattern
- Modular architecture (routes, services, models, ml)
- Repository pattern for database access
- Strategy pattern for document parsers
- Singleton pattern for services
- Graceful ML degradation

### Frontend Features
- Modern responsive UI
- Document preview modal
- Upload management
- Search result cards
- Theme toggle
- Interactive elements

### Technical Stack
- Python 3.12
- FastAPI + Uvicorn
- sentence-transformers
- PyTorch (CPU)
- SQLite
- React 19
- Create React App
- Docker & Docker Compose

## Future Roadmap

### Planned Features
- [ ] User authentication and authorization
- [ ] Document folders and tags
- [ ] Advanced search filters
- [ ] Export search results
- [ ] Batch document upload
- [ ] Admin dashboard with analytics
- [ ] Vector database integration (FAISS, Milvus)
- [ ] Multi-tenant support
- [ ] Document versioning
- [ ] OCR for scanned documents
- [ ] Collaborative features
- [ ] API rate limiting
- [ ] Elasticsearch integration
- [ ] Redis caching
- [ ] Kubernetes deployment configs

### Performance Improvements
- [ ] Horizontal scaling support
- [ ] Load balancing
- [ ] Database connection pooling
- [ ] Background job processing
- [ ] Lazy loading for large document lists
- [ ] Progressive Web App (PWA)
- [ ] Server-side rendering option

### ML Enhancements
- [ ] Hybrid search (semantic + keyword + metadata)
- [ ] Query expansion suggestions
- [ ] Cross-encoder reranking
- [ ] Custom model fine-tuning
- [ ] Domain-specific models
- [ ] Multilingual model selection UI
- [ ] Automatic language detection
- [ ] Named entity recognition
- [ ] Document summarization
- [ ] Question answering

### UX Improvements
- [ ] Advanced search syntax
- [ ] Faceted search
- [ ] Search suggestions
- [ ] Recent documents
- [ ] Favorites/bookmarks
- [ ] Document annotations
- [ ] Collaborative editing
- [ ] Activity feed
- [ ] Notifications
- [ ] Mobile app

### DevOps
- [ ] Automated testing (unit, integration, e2e)
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting
- [ ] Logging aggregation
- [ ] Performance profiling
- [ ] Automated backups
- [ ] Disaster recovery plan
- [ ] Security scanning
- [ ] Compliance checks

---

## Version Guidelines

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

## Change Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes
- **Improved**: Performance or code quality improvements
