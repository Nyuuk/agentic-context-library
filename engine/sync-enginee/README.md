# Agentix Context Library - Sync Engine

Sync engine for processing markdown documents into vector embeddings.

## Architecture

The sync engine:
1. Scans `context-registry/` for markdown documents
2. Validates `index.md` frontmatter in each folder
3. Chunks documents using recursive markdown strategy
4. Embeds chunks using BGE-M3 model
5. Upserts to Qdrant vector database
6. Detects and removes orphaned documents

## Modules

- `config.py` - Configuration management
- `scanner.py` - Folder scanning and validation
- `chunker.py` - Recursive markdown chunking
- `embedder.py` - BGE-M3 embedding integration
- `qdrant_manager.py` - Qdrant database operations
- `sync_report.py` - Sync report generation
- `sync.py` - Main orchestration script

## Usage

### Normal Sync (Skip Unchanged Files)

By default, sync-engine only processes new or modified files:

```bash
# Via Docker Compose (Recommended)
docker compose --profile sync run --rm sync-engine
```

### Force Full Re-Sync

To force re-processing of **all** files (useful for migrations or index rebuilds):

```bash
# Via CLI flag
docker compose --profile sync run --rm sync-engine --force

# Or via environment variable
FORCE_SYNC=true docker compose --profile sync run --rm sync-engine
```

**When to use `--force`:**
- After changing embedding model
- After schema changes in Qdrant
- For data migration or recovery
- To rebuild the entire vector index

> ⚠️ **Warning:** Force sync will re-embed all documents, which is resource-intensive (GPU memory + time).

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export QDRANT_URL=http://localhost:6333
export CONTEXT_ROOT=/path/to/context-registry
export EMBEDDING_MODEL=BAAI/bge-m3

# Run sync (normal)
python sync.py

# Run sync (force)
python sync.py --force
```

## Configuration

Environment variables:

- `QDRANT_URL` - Qdrant server URL (default: http://localhost:6333)
- `CONTEXT_ROOT` - Path to context registry (required)
- `EMBEDDING_MODEL` - HuggingFace model name (default: BAAI/bge-m3)
- `COLLECTION_NAME` - Qdrant collection name (default: context_library)
- `LOG_LEVEL` - Logging level (default: INFO)
- `FORCE_SYNC` - Force re-sync all files (default: false, accepts: true/false)

## Exit Codes

- `0` - Success (no errors)
- `1` - Partial or complete failure (see logs)
