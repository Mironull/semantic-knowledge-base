# Machine Learning Integration

## Overview

The backend now includes semantic search capabilities powered by sentence-transformers. The ML functionality is integrated transparently into the existing document upload and search workflows.

## Architecture

### Separate Database Design
- **Main Database** (`docstore.db`): Stores document metadata and binary content
- **Embeddings Database** (`embeddings.db`): Stores vector embeddings separately
- This separation ensures clean data isolation and independent scaling

### ML Module Structure

```
backend/app/ml/
├── __init__.py              # Module exports
├── model_registry.py        # Singleton model manager
├── embedding_service.py     # High-level embedding service
├── embedding_db.py          # Embeddings database manager
└── text_preprocessor.py     # Text cleaning and normalization
```

## Key Components

### 1. ModelRegistry (`model_registry.py`)
- **Purpose**: Manages the lifecycle of the SentenceTransformer model
- **Features**:
  - Singleton pattern for efficient memory usage
  - Automatic model loading and warm-up
  - Device management (CPU/CUDA)
  - Model metadata tracking
- **Model**: `paraphrase-multilingual-mpnet-base-v2`
  - 768-dimensional embeddings
  - Supports 50+ languages including Russian
  - ~420M parameters

### 2. EmbeddingService (`embedding_service.py`)
- **Purpose**: High-level interface for generating embeddings
- **Features**:
  - Text preprocessing integration
  - Batch processing with chunking
  - Cosine similarity computation
  - Graceful error handling
- **Methods**:
  - `generate_embedding(text)` - Single text embedding
  - `generate_embeddings_batch(texts)` - Batch processing
  - `find_most_similar(query, docs)` - Semantic search
  - `compute_similarity(emb1, emb2)` - Similarity score

### 3. TextPreprocessor (`text_preprocessor.py`)
- **Purpose**: Clean and normalize text before embedding
- **Transformations**:
  - Unicode normalization (NFC)
  - HTML tag stripping
  - URL and email removal
  - Whitespace collapsing
  - Text truncation (10,000 chars)
  - Optional lowercasing

### 4. EmbeddingDatabase (`embedding_db.py`)
- **Purpose**: Persist and retrieve vector embeddings
- **Storage**: SQLite database with BLOB fields
- **Schema**:
  ```sql
  CREATE TABLE embeddings (
      doc_id TEXT PRIMARY KEY,
      embedding BLOB NOT NULL,
      embedding_dim INTEGER NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
  ```
- **Methods**:
  - `store_embedding(doc_id, embedding)` - Save vector
  - `get_embedding(doc_id)` - Retrieve single vector
  - `get_all_embeddings()` - Bulk retrieval for search
  - `delete_embedding(doc_id)` - Remove vector

## Integration Points

### 1. Document Upload (`/upload`)
**Automatic Embedding Generation**:
1. Document uploaded and stored in main database
2. Text extracted using `DocumentParserService`
3. Text preprocessed and cleaned
4. Embedding generated using sentence-transformers
5. Embedding stored in separate embeddings database
6. Process is transparent to API clients

**Code Flow**:
```python
# 1. Store document
metadata = db_manager.insert_document(...)

# 2. Extract text
parsed_data = parser_service.parse_document(...)
text_content = parsed_data.get("content", "")

# 3. Generate and store embedding
if embedding_service.is_available():
    embedding = embedding_service.generate_embedding(text_content)
    embedding_db.store_embedding(doc_id, embedding)
```

### 2. Document Search (`/search`)
**Semantic Search with Fallback**:
1. Query embedding generated from search text
2. All document embeddings retrieved from database
3. Cosine similarity computed for all documents
4. Results sorted by similarity score
5. Top K documents returned (default: 20)
6. Falls back to filename search if ML unavailable

**Code Flow**:
```python
# 1. Generate query embedding
query_embedding = embedding_service.generate_embedding(query)

# 2. Get all document embeddings
doc_ids, doc_embeddings = embedding_db.get_all_embeddings()

# 3. Find most similar
similar_docs = embedding_service.find_most_similar(
    query_embedding, doc_embeddings, doc_ids, top_k=20
)

# 4. Retrieve metadata
results = [db_manager.get_document_metadata(doc_id)
           for doc_id, score in similar_docs]
```

## Graceful Degradation

The system handles ML unavailability gracefully:

1. **Missing Dependencies**: If `sentence-transformers` not installed:
   - Service initialization succeeds with warnings
   - Upload works normally (embeddings not generated)
   - Search falls back to filename matching

2. **Model Loading Failure**: If model fails to load:
   - Service marked as unavailable
   - All operations continue with fallback behavior

3. **Runtime Errors**: If embedding generation fails:
   - Error logged but not propagated
   - Document still saved successfully
   - Search falls back to filename matching

## Dependencies

```txt
sentence-transformers==2.2.2  # Core ML library
numpy==1.24.3                 # Vector operations
```

### Transitive Dependencies
- PyTorch (installed by sentence-transformers)
- Transformers library (Hugging Face)
- tokenizers
- scipy

## Configuration

### Model Selection
Default: `paraphrase-multilingual-mpnet-base-v2`

To use a different model, modify `EmbeddingService` initialization:
```python
embedding_service = EmbeddingService(
    model_name='all-MiniLM-L6-v2',  # Smaller, faster model
    device='cuda',                   # Use GPU if available
    enable_preprocessing=True
)
```

### Device Configuration
- **CPU**: Default, works everywhere
- **CUDA**: Requires NVIDIA GPU with CUDA support
- **MPS**: Apple Silicon (experimental)

### Preprocessing Options
```python
preprocessor = TextPreprocessor(
    lowercase=False,        # Preserve case (recommended for multilingual)
    strip_html=True,       # Remove HTML tags
    max_length=10000,      # Truncate long texts
    enable=True            # Enable preprocessing
)
```

## Performance Characteristics

### Model Loading
- **Time**: ~2-5 seconds (first load downloads model ~1.5GB)
- **Memory**: ~1.5GB RAM
- **Cached**: Subsequent loads are instant

### Embedding Generation
- **Single Text**: ~10-50ms on CPU
- **Batch (32 texts)**: ~200-500ms on CPU
- **GPU**: 5-10x faster than CPU

### Search Performance
- **100 documents**: <10ms
- **1,000 documents**: ~50ms
- **10,000 documents**: ~500ms

Note: Search scales linearly with document count. For very large datasets (>100K documents), consider using vector databases (FAISS, Milvus, Pinecone).

## Monitoring and Debugging

### Logs
The ML service prints detailed logs:
```
Loading model 'paraphrase-multilingual-mpnet-base-v2' on device 'cpu'...
Model loaded in 2.34s | dim=768 | params=420,194,304 | max_seq=512
Running warm-up inference...
Warm-up complete.
Encoded single text in 0.0234s | len=150 | norm=1.0000
Semantic search returned 15 results
```

### Health Check
Check if ML service is operational:
```python
if embedding_service.is_available():
    print("ML service ready")
    print(f"Embedding dimension: {embedding_service.get_embedding_dimension()}")
```

### Database Stats
```python
count = embedding_db.get_embedding_count()
print(f"Total embeddings stored: {count}")
```

## Example Queries

### Russian Language
- "машинное обучение" → finds ML documents in Russian
- "нейронные сети" → finds neural network documents
- "анализ данных" → finds data analysis documents

### English Language
- "neural networks" → finds related documents
- "deep learning architectures" → semantic match
- "python programming" → finds relevant code/docs

### Mixed Queries
The model handles code-switched queries:
- "python и машинное обучение"
- "API documentation для deep learning"

## Troubleshooting

### Issue: Model not loading
**Symptoms**: Warnings about unavailable ML features

**Solutions**:
1. Install dependencies: `pip install sentence-transformers numpy`
2. Check internet connection (first run downloads model)
3. Verify disk space (~1.5GB required)

### Issue: Slow embedding generation
**Symptoms**: Upload takes >10 seconds per document

**Solutions**:
1. Use GPU: Set `device='cuda'` in EmbeddingService
2. Use smaller model: `all-MiniLM-L6-v2` (384 dims, 3x faster)
3. Disable preprocessing if not needed

### Issue: Search returns irrelevant results
**Symptoms**: Low-quality semantic matches

**Solutions**:
1. Check that embeddings were generated (verify embeddings.db)
2. Ensure queries are meaningful (avoid single words)
3. Consider adjusting `top_k` parameter
4. Verify document text extraction quality

## Future Enhancements

Potential improvements:
1. **Vector Database**: Use FAISS/Milvus for large-scale deployments
2. **Hybrid Search**: Combine semantic + keyword + metadata filters
3. **Reranking**: Use cross-encoder for better result quality
4. **Batch Reindexing**: Background job to regenerate embeddings
5. **Query Expansion**: Use embeddings to suggest related queries
6. **Multilingual Models**: Support language-specific models
7. **Fine-tuning**: Domain-specific model adaptation
