"""Main sync engine script."""

import os
import sys
import logging
from datetime import datetime
from colorama import Fore, Style, init as init_colorama

from config import Config
from scanner import Scanner
from chunker import MarkdownChunker
from embedder import Embedder
from qdrant_manager import QdrantManager
from sync_report import SyncStats, SyncReporter


# Initialize colorama for colored output
init_colorama(autoreset=True)


def setup_logging(log_level: str ="INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def main() -> int:
    """Main sync engine entry point."""
    
    # Load configuration
    config = Config.from_env()
    setup_logging(config.log_level)
    
    logger = logging.getLogger(__name__)
    
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    logger.info(f"{Fore.CYAN}╔════════════════════════════════════════════════════════════════╗")
    logger.info(f"{Fore.CYAN}║  Agentix Context Library - Sync Engine                         ║")
    logger.info(f"{Fore.CYAN}╚════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    logger.info("")
    
    stats = SyncStats()
    
    try:
        # Step 1: Connect to Qdrant
        logger.info(f"{Fore.YELLOW}[1/7] Connecting to Qdrant...{Style.RESET_ALL}")
        qdrant = QdrantManager(
            qdrant_url=config.qdrant_url,
            collection_name=config.collection_name,
            vector_size=config.vector_size,
            distance_metric=config.distance_metric,
        )
        qdrant.connect()
        qdrant.ensure_collection_exists()
        
        # Step 2: Load embedding model
        logger.info(f"{Fore.YELLOW}[2/7] Loading embedding model...{Style.RESET_ALL}")
        embedder = Embedder(model_name=config.embedding_model)
        embedder.load_model()
        
        # Step 3: Scan context registry
        logger.info(f"{Fore.YELLOW}[3/7] Scanning context registry...{Style.RESET_ALL}")
        scanner = Scanner(context_root=config.context_root)
        documents, scan_errors = scanner.scan()
        
        # Record scan errors
        stats.errors.extend(scan_errors)
        stats.error_count = len(scan_errors)
        
        logger.info(f"Found {len(documents)} valid documents")
        
        # Step 4: Initialize chunker
        logger.info(f"{Fore.YELLOW}[4/7] Initializing chunker...{Style.RESET_ALL}")
        chunker = MarkdownChunker(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            min_chunk_size=config.min_chunk_size,
        )
        
        # Step 5: Process documents
        logger.info(f"{Fore.YELLOW}[5/7] Processing documents...{Style.RESET_ALL}")
        
        for doc_info in documents:
            try:
                # Check if document changed
                existing_checksum = qdrant.get_document_checksum(doc_info.relative_path)
                
                if existing_checksum == doc_info.checksum:
                    # Skip unchanged documents (unless --force is specified)
                    if not config.force_sync:
                        stats.skipped_files += 1
                        logger.info(f"{Fore.YELLOW}⏭️  Skipped (unchanged): {doc_info.relative_path}{Style.RESET_ALL}")
                        continue
                    else:
                        logger.info(f"{Fore.CYAN}🔄 Force updating: {doc_info.relative_path}{Style.RESET_ALL}")
                
                # Document is new or changed
                is_new = existing_checksum is None
                
                # Chunk document
                chunks = chunker.chunk_document(
                    content=doc_info.content,
                    path_document=doc_info.relative_path,
                )
                
                if not chunks:
                    logger.warning(f"No chunks generated for {doc_info.relative_path}")
                    stats.warnings.append(f"No chunks: {doc_info.relative_path}")
                    continue
                
                # Embed chunks
                chunk_texts = [chunk.text for chunk in chunks]
                embeddings = embedder.embed_texts(chunk_texts)
                
                # Upsert to Qdrant
                chunk_count = qdrant.upsert_chunks(doc_info, chunks, embeddings)
                
                # Update stats
                if is_new:
                    stats.added_files += 1
                    stats.added_chunks += chunk_count
                    logger.info(f"{Fore.GREEN}✅ Added: {doc_info.relative_path} ({chunk_count} chunks){Style.RESET_ALL}")
                else:
                    stats.updated_files += 1
                    stats.updated_chunks += chunk_count
                    logger.info(f"{Fore.BLUE}🔄 Updated: {doc_info.relative_path} ({chunk_count} chunks){Style.RESET_ALL}")
            
            except Exception as e:
                error_msg = f"{doc_info.relative_path}: {str(e)}"
                stats.errors.append(error_msg)
                stats.error_count += 1
                logger.error(f"{Fore.RED}❌ Error processing {doc_info.relative_path}: {e}{Style.RESET_ALL}")
        
        # Step 6: Orphan detection and cleanup
        logger.info(f"{Fore.YELLOW}[6/7] Detecting orphaned documents...{Style.RESET_ALL}")
        
        # Get all document paths from DB
        db_paths = qdrant.get_all_document_paths()
        
        # Get all document paths from filesystem
        fs_paths = {doc_info.relative_path for doc_info in documents}
        
        # Find orphans (in DB but not in filesystem)
        orphan_paths = db_paths - fs_paths
        
        if orphan_paths:
            logger.info(f"Found {len(orphan_paths)} orphaned documents")
            for orphan_path in orphan_paths:
                try:
                    deleted_count = qdrant.delete_document_chunks(orphan_path)
                    stats.deleted_files += 1
                    stats.deleted_chunks += deleted_count
                    logger.info(f"{Fore.MAGENTA}🗑️  Deleted orphan: {orphan_path} ({deleted_count} chunks){Style.RESET_ALL}")
                except Exception as e:
                    logger.error(f"Failed to delete orphan {orphan_path}: {e}")
        else:
            logger.info("No orphaned documents found")
        
        # Step 7: Generate report
        logger.info(f"{Fore.YELLOW}[7/7] Generating sync report...{Style.RESET_ALL}")
        logger.info("")
        
        total_chunks = qdrant.get_total_points()
        
        report = SyncReporter.generate_report(
            stats=stats,
            qdrant_url=config.qdrant_url,
            context_root=config.context_root,
            collection_name=config.collection_name,
            embedding_model=config.embedding_model,
            total_chunks_in_db=total_chunks,
        )
        
        # Determine exit code
        if stats.error_count > 0:
            logger.warning(f"{Fore.YELLOW}Sync completed with {stats.error_count} errors{Style.RESET_ALL}")
            return 1
        else:
            logger.info(f"{Fore.GREEN}Sync completed successfully!{Style.RESET_ALL}")
            return 0
    
    except Exception as e:
        logger.error(f"{Fore.RED}Fatal error: {e}{Style.RESET_ALL}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
