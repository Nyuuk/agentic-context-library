# Agentix Context Library

> **AI-Powered Context Registry** - Single Source of Truth for AI Agents

A vector database-powered context library that provides AI agents with semantic access to organizational standards, best practices, and technical documentation.

## 🎯 Overview

**Agentix Context Library** enables AI agents to:
- 🔍 **Search semantically** across organizational knowledge
- 📚 **Access standards** and best practices via MCP protocol
- 🚀 **Stay updated** automatically with git-based versioning
- 🌐 **Support multilingual** content (Indonesian & English)

## 🏗️ Architecture

```
┌─────────────────┐
│ Context Registry│ ◄── Git-based markdown documents
│  (Markdown)     │
└────────┬────────┘
         │
    ┌────▼──────┐
    │Sync Engine│ ◄── BGE-M3 embeddings (1024-dim)
    └────┬──────┘
         │
    ┌────▼───────┐
    │   Qdrant   │ ◄── Vector database (Cosine similarity)
    │  Vector DB │
    └────┬───────┘
         │
    ┌────▼──────┐
    │MCP Server │ ◄── AI Agent interface
    └───────────┘
```

**Components:**
1. **Context Registry** - Git-versioned markdown knowledge base
2. **Sync Engine** - One-shot processor (scan → chunk → embed → upsert)
3. **Qdrant** - Self-hosted vector database
4. **MCP Server** - AI agent integration via Model Context Protocol

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- 4GB RAM minimum (for BGE-M3 model)

### 1. Clone Repository

```bash
git clone <repository-url>
cd agentix-context-library
```

### 2. Start Services

```bash
# Start Qdrant vector database
docker compose up -d qdrant

# Run initial sync (downloads BGE-M3 model on first run ~2.27GB)
docker compose run --rm sync-engine

# Start MCP server (for AI agents)
docker compose up -d mcp-server
```

### 3. Verify Installation

```bash
# Check Qdrant dashboard
open http://localhost:6333/dashboard

# View sync status
docker compose logs sync-engine
```

## 📁 Project Structure

```
agentix-context-library/
├── context-registry/          # Knowledge base (markdown files)
│   ├── backend/
│   │   └── auth/              # Authentication standards
│   │       ├── index.md       # Folder metadata
│   │       ├── keycloak-setup.md
│   │       └── jwt-standard.md
│   └── infrastructure/
│       └── kubernetes/        # K8s best practices
│           ├── index.md
│           └── cluster-setup.md
│
├── engine/
│   ├── sync-engine/           # Document processor
│   │   ├── config.py          # Configuration
│   │   ├── scanner.py         # Folder traversal + validation
│   │   ├── chunker.py         # Recursive markdown chunking
│   │   ├── embedder.py        # BGE-M3 integration
│   │   ├── qdrant_manager.py  # Vector DB operations
│   │   ├── sync_report.py     # Reporting
│   │   └── sync.py            # Main orchestrator
│   │
│   └── mcp-server/            # AI agent server
│       └── server.py          # MCP protocol implementation
│
├── docs/                      # Documentation
│   ├── prd.md                 # Product requirements
│   ├── user-stories.md        # User stories
│   ├── contributor-guide.md   # Contribution guide
│   ├── MODEL_CACHE.md         # Model caching strategy
│   └── templates/
│       └── index-template.md  # Template for new folders
│
└── docker-compose.yml         # Service orchestration
```

## 📝 Adding Content

### Create New Topic Folder

```bash
# 1. Create folder structure
mkdir -p context-registry/backend/database
cd context-registry/backend/database

# 2. Create index.md with frontmatter
cat > index.md << 'EOF'
---
title: "Database Standards"
version: "1.0.0"
status: "stable"
language: "en"
tags:
  - database
  - postgresql
  - migrations
---

# Database Standards

Overview of database best practices...
EOF

# 3. Add content files
echo "# PostgreSQL Setup Guide..." > postgres-setup.md

# 4. Sync to vector database
docker compose run --rm sync-engine
```

### Metadata Schema

Every folder **must** have `index.md` with YAML frontmatter:

```yaml
---
title: "Topic Title"           # Required
version: "1.0.0"               # Required (SemVer format)
status: "draft|stable|deprecated"  # Required
language: "id|en"              # Required
tags:                          # Optional
  - tag1
  - tag2
---
```

## 🔧 Configuration

Environment variables (`.env`):

```bash
# Qdrant
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=context_library

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-m3

# Context Registry
CONTEXT_ROOT=/data/context-registry

# Logging
LOG_LEVEL=INFO
```

## 🔄 Sync Workflow

**Trigger sync when:**
- Adding new documents
- Updating existing content
- Deleting outdated information

**Sync process:**
```bash
docker compose run --rm sync-engine
```

**What happens:**
1. Scans `context-registry/` for markdown files
2. Validates `index.md` frontmatter
3. Chunks documents (recursive by headers, fallback 512 tokens)
4. Embeds with BGE-M3 (1024-dim vectors)
5. Upserts to Qdrant (delete old + insert new)
6. Detects and removes orphaned documents
7. Generates sync report

## 🧪 Testing

### Verify Sync Engine

```bash
# Run sync
docker compose run --rm sync-engine

# Expected output:
#  ✅ Added:   5 files  (14 chunks)
#  Duration: 1m 17s
#  Total chunks in DB: 14
```

### Query Qdrant

```bash
# Open Qdrant console
open http://localhost:6333/dashboard

# Collection: context_library
# Points: ~14 (from sample data)
# Vector size: 1024
# Distance: Cosine
```

## 🐛 Troubleshooting

### Model Download Slow

BGE-M3 model (~2.27GB) downloads on first run and is cached in Docker volume `agentix-huggingface-cache`.

**Speed up:**
```bash
# Pre-download model locally
mkdir -p models
python3 -c "
from sentence_transformers import SentenceTransformer
import os
os.environ['HF_HOME'] = './models'
SentenceTransformer('BAAI/bge-m3')
"

# Then mount in docker-compose.yml:
# - ./models:/root/.cache/huggingface:ro
```

### Rebuild is Slow

Model is cached in persistent volume - rebuilds should be ~6 seconds.

**If slow:**
```bash
# Check volume exists
docker volume ls | grep huggingface-cache

# Rebuild
docker compose build sync-engine
```

### Sync Errors

**Common issues:**
1. **Invalid frontmatter** - Check YAML syntax in `index.md`
2. **Wrong SemVer** - Version must be `X.Y.Z` format
3. **Missing index.md** - Every folder needs `index.md`

**Debug:**
```bash
# View detailed logs
docker compose run --rm sync-engine 2>&1 | tee sync.log
```

## 📊 Performance

**Sync Engine:**
- 5 documents → 14 chunks → ~1m 17s
- BGE-M3 loading: ~30s (from cache)
- Embedding: ~10-15s per file
- Qdrant upsert: ~5-10s per file

**Model Cache:**
- First run: ~3 minutes (download 2.27GB)
- Subsequent runs: instant (from volume)
- Build time: ~6 seconds (with cached deps)

## 🛠️ Development

### Run Locally (Without Docker)

```bash
# Sync Engine
cd engine/sync-engine
pip install -r requirements.txt

export QDRANT_URL=http://localhost:6333
export CONTEXT_ROOT=../../context-registry
export EMBEDDING_MODEL=BAAI/bge-m3

python sync.py
```

## 📄 License

[Your License Here]

## 🤝 Contributing

See [`docs/contributor-guide.md`](docs/contributor-guide.md) for:
- Folder structure rules
- Frontmatter requirements
- Content guidelines
- Versioning strategy

## 📚 Documentation

- [Product Requirements](docs/prd.md)
- [User Stories](docs/user-stories.md)
- [Contributor Guide](docs/contributor-guide.md)
- [Model Caching Strategy](docs/MODEL_CACHE.md)

## 🔗 Related Projects

- [Qdrant](https://qdrant.tech/) - Vector database
- [BGE-M3](https://huggingface.co/BAAI/bge-m3) - Embedding model
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol
