#!/usr/bin/env python3
"""
Agentix Context Library - MCP Server

Provides AI agents with semantic search and document access via MCP protocol.
Tools: search_context, read_content, list_directory, get_metadata

Framework: FastMCP (jlowin/fastmcp)
Auth: BearerTokenAuth via MCP_API_KEY environment variable
"""

import os
import logging
from typing import List, Dict, Optional

from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from sentence_transformers import SentenceTransformer


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "context_library")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "1024"))
MCP_API_KEY = os.getenv("MCP_API_KEY")

# Initialize FastMCP with StaticTokenVerifier (Bearer Token)
if MCP_API_KEY:
    # StaticTokenVerifier expects a dict where keys are tokens and values are user info
    logger.info("Initializing MCP Server with Bearer Token Auth")
    auth = StaticTokenVerifier(tokens={
        MCP_API_KEY: {
            "username": "admin",
            "role": "admin",
            "client_id": "admin-client" 
        }
    })
else:
    logger.warning("MCP_API_KEY not set. Server running WITHOUT authentication.")
    auth = None

mcp = FastMCP(
    name="Agentix Context Library",
    auth=auth,
)

# Global instances (initialized on startup)
qdrant_client: Optional[QdrantClient] = None
embedding_model: Optional[SentenceTransformer] = None


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

    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info(f"Model loaded. Dimension: {embedding_model.get_sentence_embedding_dimension()}")


@mcp.tool()
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


@mcp.tool()
def read_content(path_document: str) -> Dict:
    """
    Read full content of a document with metadata.

    Args:
        path_document: Relative path to document (e.g., "backend/auth/keycloak-setup.md")

    Returns:
        Document content and metadata from parent index.md
    """
    if not qdrant_client:
        raise RuntimeError("Server not initialized.")

    results, _ = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="path_document", match=MatchValue(value=path_document)),
                FieldCondition(key="chunk_index", match=MatchValue(value=0))
            ]
        ),
        limit=1,
        with_payload=True
    )

    if not results:
        raise FileNotFoundError(
            f"Document not found in vector database: {path_document}. "
            f"Use list_directory to browse available documents."
        )

    # Extract content and metadata
    payload = results[0].payload
    content = payload.get("full_content")

    # Fallback if full_content is missing
    if content is None:
        content = payload.get("chunk_text", "") + "\n\n[WARNING: Full content not found in Vector DB. Showing partial chunk.]"

    metadata = {
        "title": payload.get("title", ""),
        "version": payload.get("version", ""),
        "status": payload.get("status", ""),
        "language": payload.get("language", ""),
        "tags": payload.get("tags", [])
    }

    logger.info(f"Read document from DB: {path_document} ({len(content)} bytes)")

    return {
        "path_document": path_document,
        "content": content,
        "metadata": metadata,
        "size_bytes": len(content.encode("utf-8"))
    }


@mcp.tool()
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

    results, _ = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="directory_group", match=MatchValue(value=directory_group))]
        ),
        limit=1000,
        with_payload=True
    )

    # Extract unique file paths
    files = set()
    metadata = {}

    for point in results:
        path_doc = point.payload.get("path_document")
        if path_doc:
            files.add(path_doc)

        # Capture metadata from any chunk (they share the same folder metadata)
        if not metadata and point.payload.get("status"):
            metadata = {
                "title": point.payload.get("title", ""),
                "version": point.payload.get("version", ""),
                "status": point.payload.get("status", ""),
                "language": point.payload.get("language", ""),
                "tags": point.payload.get("tags", [])
            }

    logger.info(f"Listed directory via DB: {directory_group} ({len(files)} files)")

    return {
        "directory_group": directory_group,
        "files": sorted(list(files)),
        "subdirectories": [],
        "metadata": metadata
    }


@mcp.tool()
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

    # Run MCP server with HTTP transport (bind to 0.0.0.0 for Docker)
    logger.info("Starting Agentix Context Library MCP Server...")
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/mcp",
        log_level="info"
    )
