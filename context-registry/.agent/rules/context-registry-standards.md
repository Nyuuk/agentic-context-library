
# Context Registry Standards Rule

This rule enforces strict guidelines for contributors (especially AI Agents) when adding or modifying documentation in the `agentix-context-library/context-registry`. The goal is to maintain a highly structured, machine-searchable, and consistent knowledge base.

## 1. Directory Structure (Mandatory)

All documentation MUST be placed in one of the approved top-level domain folders.

**APPROVED FOLDERS:**
- `engineering/`: Software development, DevOps, Architecture.
- `product/`: Product requirements, roadmaps, strategies.
- `it-ops/`: Infrastructure definitions, operational policies.
- `general/`: Shared glossaries, global rules, ethics.

**PROHIBITED:**
- Creating files directly in the root `context-registry/` directory.
- Creating new top-level folders without explicit approval.

## 2. The `index.md` Mandate

**EVERY FOLDER** (nested or top-level) MUST contain an `index.md` file. This is critical for the Sync Engine's metadata inheritance.

**Format:**
```yaml
---
title: "Descriptive Title"     # Required: String
version: "1.0.0"               # Required: SemVer
status: stable                 # Required: draft | stable | deprecated
language: en                   # Required: en | id
tags: [tag1, tag2]             # Optional: Array of strings
---
```

**Rule:**
- If you create a new folder (e.g., `engineering/projects/new-app`), you **MUST** immediately create `engineering/projects/new-app/index.md` with valid frontmatter.

## 3. File Placement Guidelines

- **PRDs & Architecture**:
  - **Path**: `engineering/projects/<category>/<project-name>/`
  - **Examples**: `engineering/projects/digital-identity/datarepo-service/prd.md`
  
- **Infrastructure Definitions**:
  - **Path**: `it-ops/infrastructure/<component>/`
  - **Examples**: `it-ops/infrastructure/keycloak/v24-standard.md`

- **Rules & Policies**:
  - **Path**: `<domain>/rules/`
  - **Examples**: `engineering/rules/coding-standards.md`

## 4. Content Standards (`.md`)

- **Headers**: Use valid markdown headers (`#`, `##`, `###`) to structure content. The Sync Engine splits chunks based on these headers.
- **No Frontmatter on Docs**: Regular `.md` files (non-index) DO NOT need YAML frontmatter. They inherit metadata from their parent folder's `index.md`.
- **Naming**: Use `kebab-case` for all filenames and folders.
  - ✅ `user-guide.md`
  - ❌ `User Guide.md`
  - ❌ `userGuide.md`

## 5. Agent Behavior Protocol

When an AI Agent is asked to document a system:

1.  **Analyze Domain**: Determine if it belongs in `engineering`, `product`, or `it-ops`.
2.  **Check Project**: Does the project folder exist?
    -   **No**: Create folder + Create `index.md`.
    -   **Yes**: Proceed.
3.  **Create Document**: Write the content in markdown.
4.  **Verify**: Ensure no files are "orphaned" in the root directory.
