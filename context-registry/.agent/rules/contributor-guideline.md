---
trigger: model_decision
description: Guideline if want to contrib / add document to context-registry
---

# Contributor Guideline — Agentix Context Library

> Complete guide for adding, updating, and managing documents in the **Context Registry** for Agentix Context Library.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Folder Structure](#folder-structure)
3. [index.md Format](#indexmd-format)
4. [Adding New Topics](#adding-new-topics)
5. [Adding Documents to Existing Topics](#adding-documents-to-existing-topics)
6. [Updating Documents](#updating-documents)
7. [Deleting Documents](#deleting-documents)
8. [Versioning (SemVer)](#versioning-semver)
9. [Status Lifecycle](#status-lifecycle)
10. [Rules and Validation](#rules-and-validation)
11. [FAQ](#faq)

---

## Core Concepts

### How the System Works

```
┌─────────────────────┐       ┌──────────────┐       ┌──────────────┐
│   Context Registry  │──────▶│  Sync Engine │──────▶│  Vector DB   │
│   (Git Repository)  │       │  (Chunking + │       │  (Semantic   │
│                     │       │   Embedding) │       │   Search)    │
│  You write          │       │              │       │              │
│  documents here     │       │  Automatically│       │  AI Agent    │
│                     │       │  processes    │       │  searches    │
│                     │       │  documents    │       │  from here   │
└─────────────────────┘       └──────────────┘       └──────────────┘
```

1. **You** write Markdown documents in Context Registry
2. **Sync Engine** automatically processes documents into vectors
3. **AI Agent** searches information from Vector DB to answer questions

### Core Principles

- **One folder = One topic** — Each folder represents a single topic/domain
- **`index.md` = Folder identity** — Every folder MUST have `index.md` with metadata
- **Regular files = Frictionless** — `.md` files other than `index.md` DON'T need frontmatter
- **Metadata inheritance** — All files in a folder automatically inherit metadata from `index.md`

---

## Folder Structure

### Basic Rules

| Rule | Description |
|---|---|
| Every folder MUST have `index.md` | Folders without `index.md` will be skipped by Sync Engine |
| Files MUST be inside folders | `.md` files directly in context-registry root are **NOT allowed** |
| Unlimited nested depth | Folders can be nested as deep as needed |
| Folder naming: lowercase + dash | Example: `backend-services/`, not `Backend Services/` |

### Example Structure

```
context-registry/
│
├── backend/
│   ├── index.md                          ← Metadata for "backend" topic
│   ├── overview.md                       ← Regular content (no frontmatter)
│   │
│   ├── auth/
│   │   ├── index.md                      ← Metadata for "auth" sub-topic
│   │   ├── keycloak-setup.md
│   │   ├── jwt-standard.md
│   │   └── oauth2-flow.md
│   │
│   └── database/
│       ├── index.md
│       ├── postgresql.md
│       └── migration-policy.md
│
├── infrastructure/
│   ├── index.md
│   └── kubernetes/
│       ├── index.md
│       ├── cluster-setup.md
│       └── networking/
│           ├── index.md                  ← Nested folders still processed
│           ├── ingress.md
│           └── service-mesh.md
│
└── policies/
    ├── index.md
    ├── naming-convention.md
    └── code-review.md
```

---

## index.md Format

### Template

```markdown
---
title: "Topic Title"
version: "1.0.0"
status: stable
language: en
tags: [tag1, tag2, tag3]
---

# Topic Title

Brief overview of what this folder/topic covers.

## Related Documents

- `file-one.md` — Brief description
- `file-two.md` — Brief description
```

### Frontmatter Fields

| Field | Required | Type | Example | Description |
|---|---|---|---|------|
| `title` | ✅ Yes | string | `"Keycloak Authentication"` | Topic/folder title |
| `version` | ✅ Yes | string (SemVer) | `"1.2.0"` | Document version, format `X.Y.Z` |
| `status` | ✅ Yes | enum | `stable` | Status: `draft`, `stable`, or `deprecated` |
| `language` | ✅ Yes | enum | `en` | Language: `id` (Indonesian) or `en` (English) |
| `tags` | ❌ Optional | array | `[auth, keycloak]` | Tags for filtering |

### Real-World Example

```markdown
---
title: "Kubernetes Cluster Standards"
version: "2.1.0"
status: stable
language: en
tags: [kubernetes, k8s, cluster, infrastructure]
---

# Kubernetes Cluster Standards

This document defines standards for configuring and managing
Kubernetes clusters in the organization.

## Documents in This Folder

- `cluster-setup.md` — Guide for setting up new clusters
- `helm-standards.md` — Standards for using Helm charts
- `networking/` — Sub-topic about networking (see `networking/index.md`)
```

---

## Adding New Topics

### Steps

1. **Create folder** in the appropriate location in the hierarchy:
   ```bash
   mkdir -p context-registry/backend/caching
   ```

2. **Create `index.md`** with frontmatter:
   ```bash
   cat > context-registry/backend/caching/index.md << 'EOF'
   ---
   title: "Caching Strategy"
   version: "1.0.0"
   status: draft
   language: en
   tags: [caching, redis, performance]
   ---

   # Caching Strategy

   Standards and guidelines for implementing caching in backend services.

   ## Related Documents

   - `redis-setup.md` — Redis setup guide
   - `cache-invalidation.md` — Cache invalidation strategy
   EOF
   ```

3. **Add supporting files** (optional):
   ```bash
   # This file DOES NOT need frontmatter
   cat > context-registry/backend/caching/redis-setup.md << 'EOF'
   # Redis Setup Guide

   ## Prerequisites

   - Redis 7.x or newer
   - Minimum 2GB dedicated RAM

   ## Installation

   ...content...
   EOF
   ```

4. **Commit & push:**
   ```bash
   git add .
   git commit -m "feat: add caching strategy documentation"
   git push
   ```

5. **Run Sync Engine** (manual):
   ```bash
   # Detailed command will be determined during Sync Engine implementation
   python sync.py --source /path/to/context-registry
   ```

---

## Adding Documents to Existing Topics

### Steps

1. **Create new `.md` file** in a folder that already has `index.md`:
   ```bash
   cat > context-registry/backend/auth/saml-integration.md << 'EOF'
   # SAML Integration Guide

   ## Overview

   Guide for integrating SAML 2.0 for Single Sign-On.

   ## Configuration Steps

   1. Setup Identity Provider
   2. Configure Service Provider
   ...
   EOF
   ```

   > ⚠️ **NO frontmatter needed!** This file automatically inherits metadata from `backend/auth/index.md`.

2. **(Optional) Update `index.md`** to list the new file:
   ```markdown
   ## Related Documents
   
   - `keycloak-setup.md` — Keycloak setup
   - `jwt-standard.md` — JWT standards
   - `saml-integration.md` — SAML integration guide    ← ADD THIS
   ```

3. **Commit & push**, then run Sync Engine.

---

## Updating Documents

### Updating Regular File Content

Simply edit the file, commit, and push. Sync Engine will automatically detect checksum changes.

```bash
# Edit file
vim context-registry/backend/auth/keycloak-setup.md

# Commit
git commit -am "fix: update keycloak setup steps"
```

> 💡 **No need to modify `index.md`** for minor changes to regular files.

### Updating Metadata / Status in index.md

Use this when there are significant changes to the topic as a whole:

```bash
# Edit index.md
vim context-registry/backend/auth/index.md
```

```yaml
---
title: "Authentication Standards"
version: "1.1.0"          # ← Bump version according to change level
status: stable
language: en
tags: [auth, keycloak, jwt, saml]    # ← Add new tags if needed
---
```

> ⚠️ **Important:** When `index.md` is updated, Sync Engine will update metadata for ALL files in that folder.

---

## Deleting Documents

### Method 1: Soft Delete (Deprecated)

Use for documents that may still be needed as historical reference.

```yaml
# In index.md, change status:
---
title: "Legacy Auth Method"
version: "1.3.0"
status: deprecated          # ← Change from stable to deprecated
language: en
tags: [auth, legacy]
---
```

> AI Agents will **NOT use** deprecated documents unless explicitly requested.

### Method 2: Hard Delete

Use for documents that are truly no longer relevant.

```bash
# Delete single file
rm context-registry/backend/auth/old-method.md

# Or delete entire folder/topic
rm -rf context-registry/backend/legacy-system/

# Commit & push
git commit -am "chore: remove legacy system documentation"
git push
```

Sync Engine will delete all related chunks from Vector DB on the next sync.

---

## Versioning (SemVer)

Format: **`MAJOR.MINOR.PATCH`** (example: `2.1.3`)

| Change | Level | Example | When to Use |
|---|---|---|------|
| Complete restructuring | **MAJOR** | `1.0.0` → `2.0.0` | Architecture change, breaking change |
| Significant additions | **MINOR** | `2.0.0` → `2.1.0` | Add new documents, new features |
| Minor fixes | **PATCH** | `2.1.0` → `2.1.1` | Fix typos, clarifications, minor updates |

### When to Bump Version?

- ✅ **Bump** when there are significant changes to the topic
- ✅ **Bump** when adding/removing files in the folder
- ✅ **Bump** when changing tags or status
- ❌ **No need to bump** if only fixing typos in one regular file (but you can bump patch)

---

## Status Lifecycle

```
  ┌──────────┐         ┌──────────┐         ┌──────────────┐
  │  draft   │────────▶│  stable  │────────▶│  deprecated  │
  └──────────┘         └──────────┘         └──────────────┘
       │                     │
       │                     ▼
       │               (update content,
       │                bump version,
       │                stay stable)
       │
       └── New document not yet
           validated/reviewed
```

| Status | Synced to DB? | AI Agent Behavior |
|---|---|---|
| `draft` | ✅ Yes | Agent MAY use, but **MUST clarify** it's a draft document |
| `stable` | ✅ Yes | Agent uses as **primary reference** |
| `deprecated` | ✅ Yes | Agent **DOES NOT use**, unless explicitly requested by user |

---

## Rules and Validation

### ✅ What You MUST Do

- Every folder MUST have `index.md` with valid frontmatter
- Use folder naming: **lowercase, dash-separated** (`my-topic/`)
- Use file naming: **lowercase, dash-separated** (`my-document.md`)
- Write clear, well-structured content using Markdown headings
- Bump version in `index.md` when there are significant changes

### ❌ What You MUST NOT Do

- Place `.md` files directly in `context-registry/` root without a folder
- Create folders without `index.md`
- Add frontmatter to files other than `index.md`
- Use `version` that doesn't follow SemVer format (`X.Y.Z`)
- Use `status` other than `draft`, `stable`, or `deprecated`

---

## FAQ

### Q: Do I need frontmatter in every file?
**A:** No. Frontmatter is only needed in `index.md`. Regular `.md` files don't need frontmatter.

### Q: What if I forget to create `index.md`?
**A:** Sync Engine will SKIP that folder and give a warning. All files in that folder won't be processed until `index.md` is created.

### Q: Can AI Agent find `draft` documents?
**A:** Yes, but the agent will clarify to the user that the document is still draft and not validated.

### Q: What if I move a file to another folder?
**A:** Sync Engine will detect this as: (1) new file in destination folder, and (2) missing file in source folder. Old chunks are deleted, new chunks created with destination folder metadata.

### Q: What file formats are supported?
**A:** Currently only **Markdown (`.md`)** files are supported.

---

## Best Practices

1. **Use descriptive titles** — Make them clear and searchable
2. **Keep documents focused** — One topic per folder
3. **Update version consciously** — Follow SemVer rules
4. **Review before marking stable** — Draft → Stable transition should be deliberate
5. **Use tags strategically** — Help AI Agents filter effectively
6. **Write in clear English** — Ensure language consistency with frontmatter
7. **Link related documents** — Cross-reference in document lists
8. **Test after sync** — Verify documents are correctly indexed in Vector DB
