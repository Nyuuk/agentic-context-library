---
trigger: always_on
description: >
  Enforces a docs-first approach — the agent MUST read existing project documentation
  in ./docs/ before performing any analysis, design, implementation, or recommendation.
  This prevents hallucination by grounding all outputs in real project data.
type: RULE
origin: CONCEPTUAL
created_at: 2026-02-14
scope: Project-Wide
---

# 🚨 Docs-First Rule (Anti-Hallucination)

> **Before performing ANY analysis, design, implementation, or recommendation, you MUST:**

1. **Scan `./docs/`**: Use `list_dir` or `find_by_name` to discover all `.md` files in the project's `./docs/` directory (and subdirectories).
2. **Read relevant docs**: Use `view_file` to read every document that could be relevant to the current task (architecture docs, data schemas, API docs, decision records, etc.).
3. **Cross-reference**: Ground ALL your outputs in the information found in these docs. If a doc conflicts with your general knowledge, **the doc is the source of truth** for this project.
4. **Cite**: When making recommendations or decisions, explicitly reference which doc informed your reasoning (e.g., "Based on `docs/architecture.md`, the current setup uses...").
5. **Flag gaps**: If the docs are missing critical information, explicitly call it out and ask the user before assuming.

> [!CAUTION]
> **NEVER** generate advice, schemas, or configurations based purely on general knowledge. Always anchor to existing project documentation first. If no docs exist, state this clearly and ask the user for context before proceeding.
