"""Qdrant client manager for vector database operations."""

from typing import List, Dict, Optional, Set
import hashlib
import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from scanner import DocumentInfo
from chunker import Chunk

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manages Qdrant vector database operations."""
    
    def __init__(
        self,
        qdrant_url: str,
        collection_name: str,
        vector_size: int = 1024,
        distance_metric: str = "Cosine",
    ):
        """Initialize Qdrant client."""
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance_metric = distance_metric
        
        self.client = None
    
    def connect(self) -> None:
        """Establish connection to Qdrant."""
        logger.info(f"Connecting to Qdrant at {self.qdrant_url}")
        try:
            self.client = QdrantClient(url=self.qdrant_url)
            logger.info("Connected to Qdrant successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def ensure_collection_exists(self) -> None:
        """Create collection if it doesn't exist."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return
            
            # Create collection with schema
            logger.info(f"Creating collection '{self.collection_name}'")
            
            # Map distance metric string to Qdrant enum
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclidean": Distance.EUCLID,
                "Dot": Distance.DOT,
            }
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=distance_map.get(self.distance_metric, Distance.COSINE),
                ),
            )
            
            logger.info(f"Collection '{self.collection_name}' created successfully")
        
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    def get_document_checksum(self, path_document: str) -> Optional[str]:
        """
        Get checksum of document from Qdrant if it exists.
        
        Returns None if document doesn't exist in DB.
        """
        try:
            # Query for any point with this path_document
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="path_document",
                            match=MatchValue(value=path_document),
                        )
                    ]
                ),
                limit=1,
            )
            
            if results[0]:  # results is (points, next_page_offset)
                return results[0][0].payload.get("checksum")
            
            return None
        
        except Exception as e:
            logger.warning(f"     Error getting checksum for {path_document}: {e}")
            return None
    
    def delete_document_chunks(self, path_document: str) -> int:
        """
        Delete all chunks for a document.
        
        Returns number of chunks deleted.
        """
        try:
            # Get all points for this document first to count
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="path_document",
                            match=MatchValue(value=path_document),
                        )
                    ]
                ),
                limit=1000,  # Should be enough for one document
            )
            
            count = len(results[0])
            
            # Delete by filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="path_document",
                            match=MatchValue(value=path_document),
                        )
                    ]
                ),
            )
            
            logger.debug(f"Deleted {count} chunks for {path_document}")
            return count
        
        except Exception as e:
            logger.error(f"Failed to delete chunks for {path_document}: {e}")
            return 0
    
    def upsert_chunks(
        self,
        doc_info: DocumentInfo,
        chunks: List[Chunk],
        embeddings: List[List[float]],
    ) -> int:
        """
        Upsert chunks for a document (delete old + insert new).
        
        Returns number of chunks inserted.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")
        
        # First delete existing chunks
        self.delete_document_chunks(doc_info.relative_path)
        
        # Prepare points
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            # Generate unique document_id
            doc_id = self._generate_document_id(
                doc_info.relative_path,
                chunk.chunk_index
            )
            
            # Prepare payload
            payload = {
                "document_id": doc_id,
                "path_document": doc_info.relative_path,
                "directory_group": doc_info.directory_group,
                "source_file": doc_info.source_file,
                "checksum": doc_info.checksum,
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk.text,
                "header_context": chunk.header_context,
                **doc_info.metadata.to_dict(),  # title, version, status, language, tags
            }
            
            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload=payload,
            )
            points.append(point)
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
            )
        
        logger.info(f"Upserted {len(points)} chunks for {doc_info.relative_path}")
        return len(points)
    
    def get_all_document_paths(self) -> Set[str]:
        """Get all unique path_document values from database."""
        try:
            all_paths = set()
            offset = None
            
            while True:
                results = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,
                    offset=offset,
                    with_payload=["path_document"],
                    with_vectors=False,
                )
                
                points, next_offset = results
                
                for point in points:
                    path = point.payload.get("path_document")
                    if path:
                        all_paths.add(path)
                
                if next_offset is None:
                    break
                offset = next_offset
            
            return all_paths
        
        except Exception as e:
            logger.error(f"Failed to get document paths: {e}")
            return set()
    
    def get_total_points(self) -> int:
        """Get total number of points in collection."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.points_count or 0
        except Exception as e:
            logger.error(f"Failed to get point count: {e}")
            return 0
    
    @staticmethod
    def _generate_document_id(path_document: str, chunk_index: int) -> str:
        """
        Generate unique document ID as UUID from path and chunk index.
        
        Uses UUID v5 (deterministic) with DNS namespace for consistent IDs.
        """
        # Create a deterministic identifier
        content = f"{path_document}#{chunk_index}"
        
        # Generate UUID v5 (SHA-1 based, deterministic)
        # Using DNS namespace as a standard namespace
        doc_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, content)
        
        return str(doc_uuid)
