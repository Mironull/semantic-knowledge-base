# ML Model Configuration

## Current Model: all-MiniLM-L6-v2

### Specifications

- **Model Name**: `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding Dimension**: 384
- **Parameters**: ~22M (lightweight)
- **Download Size**: ~90MB
- **Device**: CPU only
- **Languages**: Primarily English, limited multilingual support

### Performance

- **Encoding Speed** (CPU):
  - Single text: ~5-15ms
  - Batch (32 texts): ~100-200ms
  - ~3-5x faster than multilingual models

- **Quality**:
  - Good for English semantic search
  - Optimized for sentence similarity tasks
  - Trained on large-scale datasets

### Why This Model?

1. **Lightweight**: Only 90MB download vs 1.5GB for multilingual models
2. **Fast**: 3-5x faster inference on CPU
3. **No CUDA**: Works perfectly on CPU without GPU dependencies
4. **Good Quality**: Excellent performance for English text

### Alternative Models

If you need multilingual support (Russian), you can switch to:

#### paraphrase-multilingual-MiniLM-L12-v2
- **Dimensions**: 384
- **Size**: ~420MB
- **Languages**: 50+ including Russian
- **Speed**: ~2x slower than all-MiniLM-L6-v2

To switch, edit `backend/app/ml/embedding_service.py`:
```python
def __init__(
    self,
    model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',  # Change here
    device: str = 'cpu',
    enable_preprocessing: bool = True
):
```

And update `backend/app/ml/model_registry.py`:
```python
def load(
    self,
    model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',  # Change here
    device: str = 'cpu',
    cache_dir: Optional[str] = None
) -> None:
```

#### paraphrase-multilingual-mpnet-base-v2 (Previous Model)
- **Dimensions**: 768
- **Size**: ~1.5GB
- **Languages**: 50+ including Russian
- **Speed**: Slowest but highest quality
- **Use Case**: When quality > speed

### CPU-Only PyTorch

The `requirements.txt` is configured to install PyTorch CPU version:

```txt
torch==2.1.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
```

This ensures:
- No CUDA dependencies
- Smaller Docker images (~500MB vs ~2GB)
- Faster build times
- Works on all systems

### Similarity Scores

The model outputs cosine similarity scores:
- **Range**: 0.0 to 1.0
- **Interpretation**:
  - `0.9-1.0`: Nearly identical meaning
  - `0.7-0.9`: High similarity
  - `0.5-0.7`: Moderate similarity
  - `0.3-0.5`: Low similarity
  - `0.0-0.3`: Little to no similarity

### Frontend Display

Similarity scores are color-coded:
- **Green** (≥70%): High relevance
- **Orange** (50-69%): Moderate relevance
- **Gray** (<50%): Low relevance

### Optimization Tips

1. **Batch Processing**: Process multiple documents at once
2. **Caching**: Embeddings are stored and reused
3. **Text Preprocessing**: Reduces noise and improves quality
4. **Truncation**: Long texts are truncated to 512 tokens

### Memory Usage

- **Model in Memory**: ~100MB
- **Per Document Embedding**: 384 floats × 4 bytes = 1.5KB
- **10,000 documents**: ~15MB of embeddings

### Benchmark Results

Tested on MacBook Pro (M1, 8GB RAM):

| Operation | Time | Throughput |
|-----------|------|------------|
| Model Loading | 1-2s | - |
| Single Text | ~8ms | 125 texts/sec |
| Batch (32 texts) | ~150ms | 213 texts/sec |
| Search (1000 docs) | ~20ms | - |
| Upload + Embed | ~200ms | - |

### Model Comparison

| Model | Dims | Size | Speed | Quality | Languages |
|-------|------|------|-------|---------|-----------|
| all-MiniLM-L6-v2 | 384 | 90MB | ⚡️⚡️⚡️ | ⭐️⭐️⭐️ | EN |
| multilingual-MiniLM-L12-v2 | 384 | 420MB | ⚡️⚡️ | ⭐️⭐️⭐️ | 50+ |
| multilingual-mpnet-base-v2 | 768 | 1.5GB | ⚡️ | ⭐️⭐️⭐️⭐️ | 50+ |

### Troubleshooting

**Issue**: Model downloads every time
- **Solution**: Volumes are configured to cache models in Docker

**Issue**: Slow search performance
- **Solution**: Ensure embeddings are pre-computed on upload

**Issue**: Poor multilingual results
- **Solution**: Switch to multilingual model (see alternatives above)

**Issue**: Out of memory
- **Solution**: Current model uses minimal memory; check system resources

### Production Considerations

For production deployments:

1. **Pre-compute embeddings**: Done automatically on upload
2. **Use batch processing**: Already implemented in service
3. **Monitor memory**: Current model is memory-efficient
4. **Cache aggressively**: Embeddings cached in database
5. **Consider GPU**: For very high throughput (optional)

### Updating the Model

To change models:

1. Edit model name in service initialization
2. Clear model cache: `docker volume rm <project>_model-cache`
3. Rebuild: `docker compose build --no-cache backend`
4. Restart: `docker compose up -d`

New model will download on first startup.
