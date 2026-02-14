"""Scanner module for traversing context registry and validating structure."""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib

import frontmatter
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class FolderMetadata:
    """Metadata extracted from index.md frontmatter."""
    title: str
    version: str
    status: str  # draft | stable | deprecated
    language: str  # id | en
    tags: List[str]
    folder_path: str  # Relative path from context root
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Qdrant payload."""
        return {
            "title": self.title,
            "version": self.version,
            "status": self.status,
            "language": self.language,
            "tags": self.tags,
        }


@dataclass
class DocumentInfo:
    """Information about a discovered document."""
    file_path: Path  # Absolute path
    relative_path: str  # Relative to context root
    directory_group: str  # Folder path for context expansion
    source_file: str  # Filename
    checksum: str  # SHA-256 of content
    content: str  # Full markdown content
    metadata: FolderMetadata  # Inherited from parent index.md


class Scanner:
    """Scans context registry and validates documents."""
    
    SEMVER_PATTERN = re.compile(r'^\d+\.\d+\.\d+$')
    VALID_STATUSES = {"draft", "stable", "deprecated"}
    VALID_LANGUAGES = {"id", "en"}
    
    def __init__(self, context_root: str):
        """Initialize scanner with context root path."""
        self.context_root = Path(context_root)
        if not self.context_root.exists():
            raise ValueError(f"Context root does not exist: {context_root}")
    
    def scan(self) -> Tuple[List[DocumentInfo], List[str]]:
        """
        Scan context registry for valid documents.
        
        Returns:
            Tuple of (valid_documents, errors)
        """
        valid_documents = []
        errors = []
        
        # Find all folders with index.md
        for folder_path in self._find_folders_with_index():
            try:
                metadata = self._parse_index_metadata(folder_path)
                documents = self._process_folder(folder_path, metadata)
                valid_documents.extend(documents)
            except Exception as e:
                error_msg = f"Error processing folder {folder_path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return valid_documents, errors
    
    def _find_folders_with_index(self) -> List[Path]:
        """Find all folders containing index.md."""
        folders = []
        for index_file in self.context_root.rglob("index.md"):
            folders.append(index_file.parent)
        return folders
    
    def _parse_index_metadata(self, folder_path: Path) -> FolderMetadata:
        """
        Parse and validate index.md frontmatter.
        
        Raises:
            ValueError if validation fails
        """
        index_file = folder_path / "index.md"
        
        try:
            post = frontmatter.load(index_file)
        except (yaml.YAMLError, FileNotFoundError) as e:
            raise ValueError(f"Failed to parse index.md: {e}")
        
        # Extract required fields
        try:
            title = post.get("title")
            version = post.get("version")
            status = post.get("status")
            language = post.get("language")
            tags = post.get("tags", [])
        except Exception as e:
            raise ValueError(f"Missing required frontmatter fields: {e}")
        
        # Validate required fields
        if not title:
            raise ValueError("'title' is required but empty/missing")
        if not version:
            raise ValueError("'version' is required but empty/missing")
        if not status:
            raise ValueError("'status' is required but empty/missing")
        if not language:
            raise ValueError("'language' is required but empty/missing")
        
        # Validate version format (SemVer)
        if not self.SEMVER_PATTERN.match(version):
            raise ValueError(f"'version' must be SemVer format (X.Y.Z), got: {version}")
        
        # Validate status enum
        if status not in self.VALID_STATUSES:
            raise ValueError(f"'status' must be one of {self.VALID_STATUSES}, got: {status}")
        
        # Validate language enum
        if language not in self.VALID_LANGUAGES:
            raise ValueError(f"'language' must be one of {self.VALID_LANGUAGES}, got: {language}")
        
        # Get relative folder path
        relative_folder = folder_path.relative_to(self.context_root)
        
        return FolderMetadata(
            title=title,
            version=version,
            status=status,
            language=language,
            tags=tags if isinstance(tags, list) else [],
            folder_path=str(relative_folder),
        )
    
    def _process_folder(self, folder_path: Path, metadata: FolderMetadata) -> List[DocumentInfo]:
        """Process all .md files in a folder."""
        documents = []
        
        # Find all .md files (including index.md)
        md_files = list(folder_path.glob("*.md"))
        
        for md_file in md_files:
            try:
                doc_info = self._create_document_info(md_file, metadata)
                documents.append(doc_info)
                logger.info(f"Processed: {doc_info.relative_path}")
            except Exception as e:
                logger.warning(f"Skipping {md_file}: {e}")
        
        return documents
    
    def _create_document_info(self, file_path: Path, metadata: FolderMetadata) -> DocumentInfo:
        """Create DocumentInfo from file."""
        # Read content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")
        
        # Validate non-empty
        if not content.strip():
            raise ValueError("File is empty")
        
        # Calculate checksum
        checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Get paths
        relative_path = file_path.relative_to(self.context_root)
        directory_group = metadata.folder_path
        source_file = file_path.name
        
        return DocumentInfo(
            file_path=file_path,
            relative_path=str(relative_path),
            directory_group=directory_group,
            source_file=source_file,
            checksum=checksum,
            content=content,
            metadata=metadata,
        )
    
    @staticmethod
    def calculate_checksum(content: str) -> str:
        """Calculate SHA-256 checksum of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
