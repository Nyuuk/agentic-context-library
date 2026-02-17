"""Sync report generation."""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SyncStats:
    """Statistics for sync operation."""
    added_files: int = 0
    added_chunks: int = 0
    updated_files: int = 0
    updated_chunks: int = 0
    deleted_files: int = 0
    deleted_chunks: int = 0
    skipped_files: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = None
    
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if not self.end_time:
            self.end_time = datetime.now()
        return (self.end_time - self.start_time).total_seconds()
    
    def format_duration(self) -> str:
        """Format duration as human-readable string."""
        seconds = int(self.duration_seconds())
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{seconds}s"


class SyncReporter:
    """Generates sync reports."""
    
    @staticmethod
    def generate_report(
        stats: SyncStats,
        qdrant_url: str,
        context_root: str,
        collection_name: str,
        embedding_model: str,
        total_chunks_in_db: int,
    ) -> str:
        """Generate formatted sync report."""
        
        # Finalize stats
        if not stats.end_time:
            stats.end_time = datetime.now()
        
        # Build report
        lines = []
        lines.append("═" * 70)
        lines.append("  Agentix Context Library — Sync Report")
        lines.append(f"  Timestamp: {stats.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("═" * 70)
        lines.append("")
        lines.append(f"  Source:    {context_root}")
        lines.append(f"  Target:    {qdrant_url} (collection: {collection_name})")
        lines.append(f"  Model:     {embedding_model}")
        lines.append("")
        lines.append("  Results:")
        lines.append(f"  ├─ ✅ Added:   {stats.added_files} files  ({stats.added_chunks} chunks)")
        lines.append(f"  ├─ 🔄 Updated: {stats.updated_files} files  ({stats.updated_chunks} chunks)")
        lines.append(f"  ├─ 🗑️  Deleted: {stats.deleted_files} files  ({stats.deleted_chunks} chunks)")
        lines.append(f"  ├─ ⏭️  Skipped: {stats.skipped_files} files (unchanged)")
        lines.append(f"  └─ ❌ Errors:  {stats.error_count} files")
        lines.append("")
        
        # Warnings section
        if stats.warnings:
            lines.append("  Warnings:")
            for warning in stats.warnings[:5]:  # Limit to 5
                lines.append(f"  └─ ⚠️  {warning}")
            if len(stats.warnings) > 5:
                lines.append(f"     ... and {len(stats.warnings) - 5} more warnings")
            lines.append("")
        
        # Errors section
        if stats.errors:
            lines.append("  Errors:")
            for error in stats.errors[:5]:  # Limit to 5
                lines.append(f"  └─ ❌ {error}")
            if len(stats.errors) > 5:
                lines.append(f"     ... and {len(stats.errors) - 5} more errors")
            lines.append("")
        
        # Summary
        lines.append(f"  Duration: {stats.format_duration()}")
        lines.append(f"  Total chunks in DB: {total_chunks_in_db}")
        lines.append("═" * 70)
        
        report = "\n".join(lines)
        
        # Log to console
        print(report)
        
        # Also log to file logger
        logger.info(f"Sync completed in {stats.format_duration()}")
        logger.info(f"Added: {stats.added_files} files, Updated: {stats.updated_files} files, Deleted: {stats.deleted_files} files")
        
        return report
