#!/usr/bin/env python3
"""
Agentix Context Library - MCP Server

Provides AI agents with semantic search and document access via MCP protocol.
Tools: search_context, read_content, list_directory, get_metadata
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import frontmatter

from mcp_use.server import MCPServer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize MCP Server
server = MCPServer(
    name="Agentix Context Library",
    version="1.0.0",
    instructions=(
        "This server provides semantic search and document access to organizational "
        "knowledge base. Use search_context for semantic queries, read_content for "
        "full documents, list_directory for browsing, and get_metadata for document info."
    )
)

# Global instances (initialized on startup)
qdrant_client: Optional[QdrantClient] = None
embedding_model: Optional[SentenceTransformer] = None

# Configuration from environment
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "context_library")
CONTEXT_ROOT = Path(os.getenv("CONTEXT_ROOT", "./context-registry"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "1024"))


def initialize_services():
    """Initialize Qdrant client and embedding model on startup."""
    global qdrant_client, embedding_model
    
    logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
    qdrant_client = QdrantClient(url=QDRANT_URL)
    
    # Verify collection exists
    try:
        qdrant_client.get_collection(COLLECTION_NAME)
        logger.info(f"Connected to collection '{COLLECTION_NAME}'")
    except Exception as e:
        logger.warning(f"Collection '{COLLECTION_NAME}' not found. Run sync-engine first.")
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' does not exist. "
            "Please run the sync engine to initialize the database."
        ) from e
    
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"Model loaded. Dimension: {embedding_model.get_sentence_embedding_dimension()}")


@server.tool()
def search_context(
    query: str,
    top_k: int = 5,
    status: Optional[str] = None,
    directory_group: Optional[str] = None,
    language: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Dict]:
    """
    Search context library with semantic query and optional filters.
    
    Args:
        query: Natural language search query
        top_k: Number of results to return (1-20, default 5)
        status: Filter by status: "draft", "stable", or "deprecated"
        directory_group: Filter by directory group (e.g., "backend/auth")
        language: Filter by language: "id" or "en"
        tags: Filter by tags (returns docs matching ANY tag)
    
    Returns:
        List of matching chunks with metadata and relevance scores
    """
    if not qdrant_client or not embedding_model:
        raise RuntimeError("Server not initialized. Call initialize_services() first.")
    
    # Validate top_k
    top_k = max(1, min(20, top_k))
    
    # Embed query
    query_vector = embedding_model.encode(query, normalize_embeddings=True).tolist()
    
    # Build filters
    filter_conditions = []
    
    if status:
        filter_conditions.append(
            FieldCondition(key="status", match=MatchValue(value=status))
        )
    
    if directory_group:
        filter_conditions.append(
            FieldCondition(key="directory_group", match=MatchValue(value=directory_group))
        )
    
    if language:
        filter_conditions.append(
            FieldCondition(key="language", match=MatchValue(value=language))
        )
    
    if tags and len(tags) > 0:
        filter_conditions.append(
            FieldCondition(key="tags", match=MatchAny(any=tags))
        )
    
    # Create filter object
    search_filter = Filter(must=filter_conditions) if filter_conditions else None
    
    # Execute search using query_points
    logger.info(f"Searching: '{query}' (top_k={top_k}, filters={len(filter_conditions)})")
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True
    ).points
    
    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            "score": round(result.score, 4),
            "chunk_text": result.payload.get("chunk_text", ""),
            "metadata": {
                "path_document": result.payload.get("path_document"),
                "source_file": result.payload.get("source_file"),
                "directory_group": result.payload.get("directory_group"),
                "chunk_index": result.payload.get("chunk_index"),
                "title": result.payload.get("title"),
                "version": result.payload.get("version"),
                "status": result.payload.get("status"),
                "language": result.payload.get("language"),
                "tags": result.payload.get("tags", []),
            }
        })
    
    logger.info(f"Found {len(formatted_results)} results")
    return formatted_results


@server.tool()
def read_content(path_document: str) -> Dict:
    """
    Read full content of a document with metadata.
    
    Args:
        path_document: Relative path to document (e.g., "backend/auth/keycloak-setup.md")
    
    Returns:
        Document content and metadata from parent index.md
    """
    # Construct full path
    full_path = CONTEXT_ROOT / path_document
    
    if not full_path.exists():
        raise FileNotFoundError(
            f"Document not found: {path_document}. "
            f"Use list_directory to browse available documents."
        )
    
    if not full_path.is_file():
        raise ValueError(f"{path_document} is a directory, not a file.")
    
    # Read file content
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find parent folder's index.md
    parent_dir = full_path.parent
    index_path = parent_dir / "index.md"
    
    metadata = {}
    if index_path.exists():
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                metadata = {
                    "title": post.get("title", ""),
                    "version": post.get("version", ""),
                    "status": post.get("status", ""),
                    "language": post.get("language", ""),
                    "tags": post.get("tags", [])
                }
        except Exception as e:
            logger.warning(f"Failed to parse index.md metadata: {e}")
    
    logger.info(f"Read document: {path_document} ({len(content)} bytes)")
    
    return {
        "path_document": path_document,
        "content": content,
        "metadata": metadata,
        "size_bytes": len(content.encode("utf-8"))
    }


@server.tool()
def list_directory(directory_group: str) -> Dict:
    """
    List all files and subdirectories in a directory group.
    
    Args:
        directory_group: Directory path (e.g., "backend/auth" or "backend")
    
    Returns:
        Files, subdirectories, and metadata from index.md
    """
    if not qdrant_client:
        raise RuntimeError("Server not initialized.")
    
    # Query Qdrant for all documents in this directory_group
    # We'll use scroll to get all matching points
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    results, _ = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="directory_group", match=MatchValue(value=directory_group))]
        ),
        limit=1000,  # Assume max 1000 files per directory
        with_payload=True
    )
    
    # Extract unique file paths
    files = set()
    for point in results:
        path_doc = point.payload.get("path_document")
        if path_doc:
            files.add(path_doc)
    
    # Identify subdirectories
    # Check filesystem for subdirectories
    full_dir_path = CONTEXT_ROOT / directory_group
    subdirectories = []
    
    if full_dir_path.exists() and full_dir_path.is_dir():
        for item in full_dir_path.iterdir():
            if item.is_dir():
                subdirectories.append(item.name)
    
    # Read index.md metadata
    index_path = full_dir_path / "index.md" if full_dir_path.exists() else None
    metadata = {}
    
    if index_path and index_path.exists():
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                metadata = {
                    "title": post.get("title", ""),
                    "version": post.get("version", ""),
                    "status": post.get("status", ""),
                    "language": post.get("language", ""),
                    "tags": post.get("tags", [])
                }
        except Exception as e:
            logger.warning(f"Failed to parse index.md: {e}")
    
    logger.info(f"Listed directory: {directory_group} ({len(files)} files, {len(subdirectories)} subdirs)")
    
    return {
        "directory_group": directory_group,
        "files": sorted(list(files)),
        "subdirectories": sorted(subdirectories),
        "metadata": metadata
    }


@server.tool()
def get_metadata(path_document: str) -> Dict:
    """
    Get metadata for a document or directory without content.
    
    Args:
        path_document: Path to document or directory (e.g., "backend/auth/jwt-standard.md")
    
    Returns:
        Metadata including chunk count from vector database
    """
    if not qdrant_client:
        raise RuntimeError("Server not initialized.")
    
    # Query Qdrant for this document's chunks
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    results, _ = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="path_document", match=MatchValue(value=path_document))]
        ),
        limit=1000,
        with_payload=True
    )
    
    if not results:
        raise FileNotFoundError(
            f"Document not found in vector database: {path_document}. "
            "This document may not exist or hasn't been synced yet."
        )
    
    # Aggregate metadata from first chunk
    first_chunk = results[0].payload
    metadata = {
        "path_document": path_document,
        "title": first_chunk.get("title", ""),
        "version": first_chunk.get("version", ""),
        "status": first_chunk.get("status", ""),
        "language": first_chunk.get("language", ""),
        "tags": first_chunk.get("tags", []),
        "directory_group": first_chunk.get("directory_group", ""),
        "source_file": first_chunk.get("source_file", ""),
        "checksum": first_chunk.get("checksum", ""),
        "chunk_count": len(results)
    }
    
    logger.info(f"Retrieved metadata: {path_document} ({len(results)} chunks)")
    
    return metadata


if __name__ == "__main__":
    # Initialize services before starting server
    initialize_services()
    
    # Run MCP server
    logger.info("Starting Agentix Context Library MCP Server...")
    server.run(transport="streamable-http", debug=True)
