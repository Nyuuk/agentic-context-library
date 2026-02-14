# Model Cache Optimization Guide

## Problem

BGE-M3 model (~2.2GB) was being downloaded during Docker build, causing:
- Very slow rebuild times (3+ minutes)
- Re-download on every code change
- Network bandwidth waste

## Solution: Persistent Cache Volume

Model is now cached in a Docker volume that persists across rebuilds.

### How It Works

1. **Volume**: `huggingface-cache` stores downloaded models persistently
2. **Mounted to**: Both `sync-engine` and `mcp-server` containers
3. **Environment**: `HF_HOME=/root/.cache/huggingface` tells sentence-transformers where to cache

### First Run

On first run, model will be downloaded once:
```bash
docker compose run --rm sync-engine
```

Model download happens at runtime (~2.2GB, takes 2-3 minutes).

### Subsequent Runs

Model is loaded from cache volume - **instant startup**:
- No re-download
- Fast container startup
- Works even after `docker compose build`

### Benefits

- ✅ **Fast rebuilds**: Code changes only (~5-10 seconds)
- ✅ **Shared cache**: Both services use same model
- ✅ **Persistent**: Survives `docker compose down`
- ✅ **Offline-friendly**: Works without internet after first download

### Managing Cache

**View cache size:**
```bash
docker volume inspect agentix-huggingface-cache
```

**Clear cache** (forces re-download):
```bash
docker volume rm agentix-huggingface-cache
```

**Backup cache:**
```bash
docker run --rm -v agentix-huggingface-cache:/cache -v $(pwd):/backup alpine tar czf /backup/model-cache.tar.gz -C /cache .
```

**Restore cache:**
```bash
docker run --rm -v agentix-huggingface-cache:/cache -v $(pwd):/backup alpine tar xzf /backup/model-cache.tar.gz -C /cache
```

## Alternative: Pre-download Locally

If you want to pre-download model before building:

```bash
# 1. Create models directory
mkdir -p models/BAAI

# 2. Download model using Python
python3 -c "
from sentence_transformers import SentenceTransformer
import os
os.environ['HF_HOME'] = './models'
SentenceTransformer('BAAI/bge-m3')
"

# 3. Add volume mount in docker-compose.yml
# - ./models:/root/.cache/huggingface:ro
```

This gives you full control over model versions and offline deployment.
