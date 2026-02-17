"""Embedding module for BGE-M3 integration."""

from typing import List
import logging

from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class Embedder:
    """Handles text embedding using BGE-M3 model."""
    
    def __init__(self, model_name: str = "BAAI/bge-m3", batch_size: int = 32):
        """
        Initialize embedder with BGE-M3 model.
        
        Args:
            model_name: HuggingFace model identifier
            batch_size: Batch size for embedding
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self.vector_size = 1024  # BGE-M3 output dimension
    
    def load_model(self) -> None:
        """Load BGE-M3 model into memory."""
        logger.info(f"Loading embedding model: {self.model_name}")
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Dimension: {self.vector_size}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batches.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors (1024-dimensional)
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if not texts:
            return []
        
        try:
            # Embed in batches for better performance
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalization for cosine similarity
            )
            
            # Convert to list format for Qdrant
            return embeddings.tolist()
        
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
    
    def embed_single(self, text: str) -> List[float]:
        """Embed a single text."""
        return self.embed_texts([text])[0]
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding dimensions and format."""
        if not isinstance(embedding, list):
            return False
        if len(embedding) != self.vector_size:
            return False
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        return True
