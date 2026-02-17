# ADR-001: Force-Sync Pattern for Vector Database Updates

## Status
Accepted

## Date
2026-02-16

## Context

Agentix Context Library uses checksum-based change detection to skip unchanged documents during sync. However, there are scenarios where a full re-sync is necessary:

1. **Embedding Model Change:** If the embedding model is updated/changed, all vectors must be regenerated
2. **Schema Migration:** Changes to Qdrant collection schema require re-indexing
3. **Data Recovery:** Corrupted index or missing vectors need full rebuild
4. **Collection Migration:** Moving to a new collection or cluster

### The Bug

Initially, the skip logic in `sync.py` (lines 98-103) was commented out with the note `# force update for migration`. This caused **all files to update on every sync**, wasting significant resources:

- GPU memory for re-embedding unchanged documents
- CPU cycles for re-chunking
- Unnecessary writes to Qdrant
- Sync duration 5-10x longer than necessary

This was discovered on 2026-02-16 during a vector-db-specialist analysis.

## Decision

We implement a **`--force` flag** pattern to provide explicit control:

- **Default behavior:** Skip unchanged files (checksum match)
- **Force mode (`--force`):** Re-process all files regardless of checksum

### Implementation:
- CLI flag: `--force` (parsed in `config.py`)
- Environment variable: `FORCE_SYNC=true`
- Configuration: `config.force_sync` boolean field

### Code Changes:

**sync.py (lines 98-104):**
```python
if existing_checksum == doc_info.checksum:
    # Skip unchanged documents (unless --force is specified)
    if not config.force_sync:
        stats.skipped_files += 1
        logger.info(f"⏭️  Skipped (unchanged): {doc_info.relative_path}")
        continue
    else:
        logger.info(f"🔄 Force updating: {doc_info.relative_path}")
```

**config.py:**
```python
force_sync: bool = False  # Force re-sync all documents regardless of checksum

# In from_env():
force_sync = "--force" in sys.argv or os.getenv("FORCE_SYNC", "false").lower() == "true"
```

## Consequences

### Positive:
- ✅ Normal syncs are 5-10x faster (only process changed files)
- ✅ Reduced GPU memory usage (especially for BGE-M3 model)
- ✅ Explicit intent for full re-sync (no hidden behavior)
- ✅ Supports both manual (CLI flag) and automated (env var) workflows
- ✅ Better resource utilization in production

### Negative:
- ⚠️ Requires documentation to prevent misuse
- ⚠️ Users might forget to use `--force` when needed (e.g., after model change)
- ⚠️ Breaking change from previous (buggy) behavior

### Mitigation:
- Documented `--force` flag prominently in README
- Updated PRD to clarify sync policy
- Created this ADR for future reference
- Added clear warnings about when to use `--force`

## Alternatives Considered

### 1. Always Force Update (Current Buggy Behavior)
**Rejected:** Wasted resources and slow sync times are unacceptable.

### 2. Auto-Detect Model Changes
**Deferred:** More complex implementation. Could be added in future iteration by:
- Storing model name/version in Qdrant metadata
- Comparing on startup
- Auto-triggering force sync if mismatch detected

**Why deferred:** Adds complexity. Explicit `--force` flag is simpler and more transparent.

### 3. Separate `rebuild` Command
**Rejected:** More CLI complexity. `--force` flag is simpler and more intuitive. A boolean flag is easier to understand than a separate command.

## Verification

The fix was verified with:
1. ✅ Code review of skip logic restoration
2. ✅ Confirmation that `sync_report.py` already displays skipped count
3. ✅ Documentation updates (README, PRD, ADR)

### Test Plan (Pending):
- Normal sync (should skip unchanged files)
- Force sync (should update all files)
- Partial update (only modified files updated)
- Sync report validation

## References

- [Bug Analysis](file:///Users/Adnan/.gemini/antigravity/brain/66403ea8-c8ca-4715-8d2f-46657b8cdb06/sync_engine_bug_analysis.md)
- [Implementation Plan](file:///Users/Adnan/.gemini/antigravity/brain/66403ea8-c8ca-4715-8d2f-46657b8cdb06/implementation_plan.md)
- [PRD Section 10.1](file:///Users/Adnan/Documents/tnt/devops/agentix-context-library/root-agentix-context-library/docs/prd.md#L620-L648)
- [Vector DB Specialist Skill](file:///Users/Adnan/Documents/tnt/devops/agentix-context-library/root-agentix-context-library/.agent/skills/vector-db-specialist/SKILL.md)

## Future Enhancements

1. **Auto-detect embedding model changes:**
   - Store current model name/version in collection metadata
   - Compare on sync startup
   - Warn or auto-trigger `--force` if mismatch

2. **Checksum validation:**
   - Periodic validation that DB checksums match filesystem
   - Detect and report drift

3. **Incremental re-sync:**
   - Instead of full `--force`, allow `--force-filter` by status/tags/directory
   - Example: `--force-filter "status=draft"` to only re-sync draft docs
