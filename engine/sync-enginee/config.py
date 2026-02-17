"""Configuration management for sync engine."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Sync Engine configuration from environment variables."""
    
    # Required fields (no defaults)
    qdrant_url: str
    embedding_model: str
    context_root: str
    
    # Qdrant settings (with defaults)
    collection_name: str = "context_library"
    vector_size: int = 1024
    distance_metric: str = "Cosine"
    
    # Logging
    log_level: str = "INFO"
    
    # Processing
    chunk_size: int = 512  # tokens
    chunk_overlap: int = 50  # tokens
    max_chunk_size: int = 8192  # BGE-M3 max tokens
    min_chunk_size: int = 50  # tokens to merge
    
    # Force sync mode
    force_sync: bool = False  # Force re-sync all documents regardless of checksum
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        import sys
        
        # Check for --force flag in command line arguments or environment
        force_sync = "--force" in sys.argv or os.getenv("FORCE_SYNC", "false").lower() == "true"
        
        return cls(
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            collection_name=os.getenv("COLLECTION_NAME", "context_library"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
            context_root=os.getenv("CONTEXT_ROOT", "/data/context-registry"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            force_sync=force_sync,
        )
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.qdrant_url:
            raise ValueError("QDRANT_URL must be set")
        if not self.embedding_model:
            raise ValueError("EMBEDDING_MODEL must be set")
        if not os.path.exists(self.context_root):
            raise ValueError(f"Context root does not exist: {self.context_root}")
