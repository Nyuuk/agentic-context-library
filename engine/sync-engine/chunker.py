"""Chunking module for splitting markdown documents."""

from typing import List
from dataclasses import dataclass
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    chunk_index: int
    header_context: str  # Header hierarchy for context


class MarkdownChunker:
    """Chunks markdown documents using recursive strategy."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50,
        encoding_name: str = "cl100k_base",  # tiktoken encoding for token counting
    ):
        """Initialize chunker with configuration."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Initialize tiktoken encoder for accurate token counting
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoder: {e}. Using char-based approximation.")
            self.tokenizer = None
        
        # Create LangChain text splitter with markdown-aware separators
        self.splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n# ",      # H1 headers
                "\n## ",     # H2 headers
                "\n### ",    # H3 headers
                "\n#### ",   # H4 headers
                "\n\n",      # Paragraphs
                "\n",        # Lines
                " ",         # Words
                "",          # Characters
            ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._token_length,
            is_separator_regex=False,
        )
    
    def chunk_document(self, content: str, path_document: str) -> List[Chunk]:
        """
        Chunk markdown document using recursive strategy.
        
        Args:
            content: Markdown content to chunk
            path_document: Document path for logging
        
        Returns:
            List of Chunk objects
        """
        # Split using LangChain
        raw_chunks = self.splitter.split_text(content)
        
        # Process chunks: merge small ones, extract headers
        processed_chunks = []
        accumulated_text = ""
        chunk_index = 0
        
        for raw_chunk in raw_chunks:
            chunk_tokens = self._token_length(raw_chunk)
            
            # If chunk is too small, accumulate
            if chunk_tokens < self.min_chunk_size and accumulated_text:
                accumulated_text += "\n\n" + raw_chunk
                continue
            
            # If we have accumulated text, process it first
            if accumulated_text:
                header_ctx = self._extract_header_context(accumulated_text)
                processed_chunks.append(Chunk(
                    text=accumulated_text,
                    chunk_index=chunk_index,
                    header_context=header_ctx,
                ))
                chunk_index += 1
                accumulated_text = ""
            
            # Process current chunk
            if chunk_tokens >= self.min_chunk_size:
                header_ctx = self._extract_header_context(raw_chunk)
                processed_chunks.append(Chunk(
                    text=raw_chunk,
                    chunk_index=chunk_index,
                    header_context=header_ctx,
                ))
                chunk_index += 1
            else:
                # Start accumulating
                accumulated_text = raw_chunk
        
        # Don't forget last accumulated chunk
        if accumulated_text:
            header_ctx = self._extract_header_context(accumulated_text)
            processed_chunks.append(Chunk(
                text=accumulated_text,
                chunk_index=chunk_index,
                header_context=header_ctx,
            ))
        
        logger.info(f"Chunked {path_document}: {len(processed_chunks)} chunks")
        return processed_chunks
    
    def _token_length(self, text: str) -> int:
        """Calculate token count of text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: approximate 4 chars = 1 token
            return len(text) // 4
    
    def _extract_header_context(self, text: str) -> str:
        """
        Extract header hierarchy from chunk text.
        
        Example:
            "# Auth\n## Keycloak\n### Setup\n..."
            -> "Auth > Keycloak > Setup"
        """
        headers = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                # Extract header text
                header_text = line.lstrip('#').strip()
                if header_text:
                    headers.append(header_text)
        
        if headers:
            return " > ".join(headers[:3])  # Max 3 levels for context
        return ""
