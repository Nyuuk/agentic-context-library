# Product Requirements Document (PRD)
# Agentix Context Library

> **Version:** 1.0.0
> **Status:** Iplemented
> **Tanggal:** 15 Februari 2026
> **Disusun berdasarkan:** Diskusi arsitektur 14-15 Februari 2026

---

## 1. Ringkasan Eksekutif

**Agentix Context Library** adalah platform **Agentic RAG** yang menyediakan **Single Source of Truth** bagi AI Agent agar output yang dihasilkan konsisten dengan standar organisasi.

Sistem ini terdiri dari:
- **Context Registry** — Repository Git berisi dokumen Markdown terstruktur
- **Sync Engine** — Script Python one-shot untuk memproses dokumen menjadi vektor
- **Vector Database** — Qdrant sebagai penyimpanan vektor untuk semantic search
- **MCP Server** — Interface komunikasi agar AI Agent bisa mencari dan membaca dokumen

---

## 2. Tujuan & Masalah yang Diselesaikan

### Masalah
- AI Agent memberikan jawaban berdasarkan pengetahuan umum, bukan standar organisasi
- Tidak ada sumber acuan terpusat yang bisa dikonsumsi oleh AI Agent secara semantik
- Dokumen standar tersebar di berbagai tempat dan format

### Tujuan
- Menyediakan satu sumber kebenaran yang bisa dicari secara semantik oleh AI Agent
- Memastikan AI Agent memberikan jawaban yang konsisten dengan standar dan kebijakan organisasi
- Memungkinkan contributor mengelola dokumen dengan friction minimal

---

## 3. Keputusan Arsitektur

Semua keputusan berikut telah disepakati melalui diskusi:

| Aspek | Keputusan | Alasan |
|---|---|---|
| Vector Database | **Qdrant** (Docker) | Gratis, self-hosted, metadata filtering kuat, REST API |
| Embedding Model | **BGE-M3** (self-hosted) | Multilingual (ID + EN), open-source, tanpa API dependency |
| Chunking Strategy | **Recursive by Markdown headers** | Dokumen terstruktur; fallback fixed 512 tokens |
| Frontmatter | Hanya di `index.md` | Mengurangi friction contributor |
| Context Registry | Git repo terpisah | Versioning via Git, mounted ke engine |
| Sync Trigger | Manual / GitLab webhook | Sync Engine bukan service persisten |
| Delete Strategy | Soft (deprecated) + Hard (file removal) | Fleksibilitas |
| Versioning | Manual SemVer `X.Y.Z` | Contributor sadar akan perubahan |
| DB Versioning | Overwrite (hanya versi terbaru) | Git sebagai version history |
| Bahasa | Indonesia + English | BGE-M3 mendukung multilingual |
| Nested Folder | Unlimited depth | Fleksibilitas organisasi dokumen |
| File tanpa folder | Tidak diizinkan | Semua file harus dalam folder ber-`index.md` |
| Draft status | Tetap di-sync ke DB | Agent yang mengklarifikasi status draft |
| Deployment | Docker Compose | Qdrant + MCP Server persisten, Sync Engine on-demand |

---

## 4. Arsitektur Sistem

### 4.1 Diagram Arsitektur

```
                    ┌─────────────────────────┐
                    │     GitLab / Manual      │
                    │       Trigger            │
                    └────────────┬────────────┘
                                 │
                                 ▼
┌───────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Context     │    │    Sync Engine       │    │     Qdrant      │
│   Registry    │───▶│    (Python)          │───▶│   (Vector DB)   │
│   (Git Repo)  │    │                      │    │                 │
│               │    │  - Scan & Validate   │    │  - Store vectors│
│  Markdown     │    │  - Chunk (Recursive) │    │  - Metadata     │
│  documents    │    │  - Embed (BGE-M3)    │    │    filtering    │
│               │    │  - Upsert/Delete     │    │  - Semantic     │
│               │    │                      │    │    search       │
└───────────────┘    │  ONE-SHOT execution  │    │                 │
                     │  (bukan long-running)│    │  PERSISTENT     │
                     └──────────────────────┘    │  (always-on)    │
                                                 └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │   MCP Server    │
                                                 │   (Python)      │
                                                 │                 │
                                                 │  Tools:         │
                                                 │  - search       │
                                                 │  - read         │
                                                 │  - list_dir     │
                                                 │  - get_metadata │
                                                 │                 │
                                                 │  PERSISTENT     │
                                                 │  (always-on)    │
                                                 └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │   AI Agents     │
                                                 │   (20+ concurrent)
                                                 └─────────────────┘
```

### 4.2 Komponen & Tanggung Jawab

#### 4.2.1 Context Registry (Git Repository)

**Tipe:** Git repository terpisah (hosted di GitLab)

**Tanggung Jawab:**
- Menyimpan dokumen Markdown terstruktur
- Menyediakan version history via Git
- Menjadi sumber data utama untuk Sync Engine

**Struktur:**
```
context-registry/          # Root repository
├── <topic-folder>/
│   ├── index.md           # Frontmatter wajib (metadata folder)
│   ├── doc-satu.md        # Dokumen biasa (tanpa frontmatter)
│   ├── doc-dua.md
│   └── <sub-folder>/
│       ├── index.md       # Frontmatter untuk sub-folder
│       └── doc-tiga.md
└── ...
```

**Format `index.md`:**
```yaml
---
title: "Judul Topik"           # Wajib: string
version: "1.0.0"               # Wajib: SemVer X.Y.Z
status: stable                 # Wajib: draft | stable | deprecated
language: en                   # Wajib: en | id
tags: [tag1, tag2]             # Opsional: array of strings
---
```

**Aturan:**
- Setiap folder HARUS memiliki `index.md` dengan frontmatter valid
- File `.md` selain `index.md` TIDAK memerlukan frontmatter (mewarisi dari parent `index.md`)
- File di root tanpa folder TIDAK diizinkan
- Nested folder depth: unlimited
- Penamaan: lowercase, dash-separated

---

#### 4.2.2 Sync Engine (Python Script — One-Shot)

**Tipe:** Python script yang dijalankan on-demand (bukan long-running service)

**Trigger:**
- **Manual:** Jalankan script dari CLI atau Docker
- **GitLab Webhook:** Dipicu oleh push event ke branch tertentu

**Tanggung Jawab:**
1. Scan seluruh folder di context-registry
2. Validasi `index.md` di setiap folder
3. Untuk setiap file `.md`:
   - Hitung checksum (SHA-256)
   - Bandingkan dengan checksum di Qdrant
   - Jika baru/berubah → chunk → embed → upsert
   - Jika sama → skip
4. Detect & delete orphan entries (ada di DB tapi tidak di filesystem)
5. Output laporan sync

**Alur Sync Detail:**

```
START
  │
  ▼
Scan context-registry/
  │
  ▼
Untuk setiap folder:
  │
  ├─ index.md ada?
  │   ├─ TIDAK → Log WARNING, skip folder
  │   └─ YA → Validasi frontmatter
  │            ├─ INVALID → Log ERROR, skip folder
  │            └─ VALID → Baca metadata (title, version, status, language, tags)
  │
  ▼
Untuk setiap file .md di folder (termasuk index.md):
  │
  ├─ Hitung checksum SHA-256
  ├─ Cek checksum di Qdrant (by path_document)
  │   ├─ SAMA → Skip (tidak berubah)
  │   └─ BERBEDA atau BARU:
  │       ├─ Hapus chunks lama (by path_document) — OVERWRITE
  │       ├─ Chunk konten (recursive by headers, fallback 512 tokens)
  │       ├─ Embed setiap chunk (BGE-M3)
  │       └─ Upsert ke Qdrant dengan metadata lengkap
  │
  ▼
Orphan Detection:
  │
  ├─ Ambil semua path_document dari Qdrant
  ├─ Bandingkan dengan path_document di filesystem
  └─ Path di DB tapi TIDAK di filesystem → DELETE dari Qdrant
  │
  ▼
Output Sync Report:
  ├─ Added: X files (Y chunks)
  ├─ Updated: X files (Y chunks)
  ├─ Deleted: X files (Y chunks)
  ├─ Skipped: X files (unchanged)
  ├─ Errors: X files (with details)
  └─ Duration: Xs
  │
  ▼
END (exit 0 / exit 1)
```

**Deployment:**
```yaml
# Sync Engine dijalankan sebagai one-shot container
docker compose run --rm sync-engine
```

---

#### 4.2.3 Qdrant (Vector Database)

**Tipe:** Persistent service (always-on via Docker Compose)

**Versi:** Qdrant latest stable (≥ 1.7)

**Collection Schema:**

```json
{
  "collection_name": "context_library",
  "vectors": {
    "size": 1024,
    "distance": "Cosine"
  },
  "payload_schema": {
    "document_id":     { "type": "keyword" },
    "path_document":   { "type": "keyword" },
    "directory_group":  { "type": "keyword" },
    "source_file":      { "type": "keyword" },
    "title":            { "type": "keyword" },
    "version":          { "type": "keyword" },
    "status":           { "type": "keyword" },
    "language":         { "type": "keyword" },
    "tags":             { "type": "keyword" },
    "checksum":         { "type": "keyword" },
    "chunk_index":      { "type": "integer" },
    "chunk_text":       { "type": "text" }
  }
}
```

**Konfigurasi:**
- **Port:** 6333 (REST API), 6334 (gRPC)
- **Storage:** Persistent volume via Docker
- **Distance metric:** Cosine Similarity (standar untuk text embeddings)
- **Vector dimensions:** 1024 (BGE-M3 output)

---

#### 4.2.4 MCP Server (Python — Persistent Service)

**Tipe:** Persistent service (always-on via Docker Compose)

**Tanggung Jawab:**
- Menyediakan tools untuk AI Agent mengakses context library
- Berkomunikasi dengan Qdrant untuk semantic search
- Membaca file dari context-registry mount untuk konten lengkap

**Tools yang Disediakan:**

##### Tool 1: `search_context`
```
Deskripsi: Mencari dokumen yang relevan berdasarkan query semantik

Input:
  - query: string (pertanyaan/topik yang dicari)
  - filters: object (opsional)
    - status: string ("draft" | "stable" | "deprecated")
    - directory_group: string (misal: "backend/auth")
    - language: string ("id" | "en")
    - tags: array of string
  - top_k: integer (default: 5, max: 20)

Output:
  - results: array of objects
    - chunk_text: string
    - score: float (similarity score)
    - metadata:
      - path_document: string
      - directory_group: string
      - title: string
      - version: string
      - status: string
      - language: string
      - tags: array
      - chunk_index: integer
```

##### Tool 2: `read_content`
```
Deskripsi: Membaca isi lengkap suatu dokumen dari context-registry

Input:
  - path_document: string (misal: "backend/auth/keycloak-setup.md")

Output:
  - content: string (isi file Markdown lengkap)
  - metadata:
    - title: string (dari index.md parent)
    - version: string
    - status: string
    - language: string
```

##### Tool 3: `list_directory`
```
Deskripsi: Menampilkan semua file dan sub-folder di suatu directory group

Input:
  - directory_group: string (misal: "backend/auth")

Output:
  - files: array of objects
    - path_document: string
    - source_file: string
  - subdirectories: array of string
  - metadata:
    - title: string (dari index.md)
    - version: string
    - status: string
```

##### Tool 4: `get_metadata`
```
Deskripsi: Mengambil metadata suatu dokumen atau folder tanpa konten

Input:
  - path_document: string (path ke file atau folder)

Output:
  - metadata:
    - title: string
    - version: string
    - status: string
    - language: string
    - tags: array
    - checksum: string
    - chunk_count: integer (jumlah chunks di Vector DB)
```

---

## 5. Technology Stack

### 5.1 Tabel Teknologi

| Komponen | Teknologi | Versi | Bahasa | Alasan |
|---|---|---|---|---|
| Context Registry | Git (GitLab) | - | Markdown | Version control, collaboration |
| Sync Engine | Python | 3.11+ | Python | Ekosistem ML/embedding paling mature |
| Vector Database | Qdrant | ≥ 1.7 | - | Self-hosted, metadata filtering kuat, gratis |
| MCP Server | Python | 3.11+ | Python | Kompatibilitas dengan MCP SDK |
| Embedding Model | BGE-M3 | latest | - | Multilingual (ID+EN), open-source, 1024 dim |
| Containerization | Docker + Docker Compose | - | - | Deployment konsisten |

### 5.2 Embedding Model: BGE-M3

| Spesifikasi | Detail |
|---|---|
| **Model** | BAAI/bge-m3 |
| **Dimensi output** | 1024 |
| **Max token input** | 8192 tokens |
| **Bahasa** | 100+ bahasa termasuk Indonesian & English |
| **Hosting** | Self-hosted (loaded saat Sync Engine dan MCP Server berjalan) |
| **Distance metric** | Cosine Similarity |

**Catatan penting:** Model embedding yang digunakan Sync Engine **HARUS identik** dengan yang digunakan MCP Server. Ketidakcocokan model akan menyebabkan search result tidak akurat.

### 5.3 Chunking Strategy: Recursive by Markdown Headers

```
Prioritas split:
  1. Split by H1 (#)
  2. Split by H2 (##)
  3. Split by H3 (###)
  4. Jika section masih > 512 tokens → fallback split by fixed-size (512 tokens, 50 token overlap)
  5. Jika section < 50 tokens → merge dengan section sebelumnya

Setiap chunk menyimpan:
  - Header hierarchy sebagai konteks (misal: "# Auth > ## Keycloak > ### Installation")
  - Konten section
```

**Contoh:**

```markdown
# Keycloak Setup                    ← Chunk 1: "# Keycloak Setup\n## Prerequisites\n..."
                                      (jika total < 512 tokens, merge H1 + H2)
## Prerequisites
- Java 17
- PostgreSQL 15

## Installation                     ← Chunk 2: "# Keycloak Setup > ## Installation\n..."
### Download
Download dari keycloak.org...

### Configure
Edit standalone.xml...

## Troubleshooting                  ← Chunk 3: "# Keycloak Setup > ## Troubleshooting\n..."
### Common Errors
...
```

---

## 6. Metadata Schema

Setiap chunk yang disimpan di Qdrant memiliki metadata (payload) berikut:

| Field | Tipe | Sumber | Contoh | Deskripsi |
|---|---|---|---|---|
| `document_id` | `keyword` | Auto | `sha256(path + chunk_idx)` | Primary key untuk upsert |
| `path_document` | `keyword` | Auto (dari filepath) | `backend/auth/keycloak.md` | Path relatif terhadap root context-registry |
| `directory_group` | `keyword` | Auto (dari folder) | `backend/auth` | Folder path untuk context expansion & filtering |
| `source_file` | `keyword` | Auto (dari filename) | `keycloak.md` | Nama file asal |
| `title` | `keyword` | `index.md` frontmatter | `Authentication Standards` | Judul topik folder |
| `version` | `keyword` | `index.md` frontmatter | `1.2.0` | Versi SemVer dokumen |
| `status` | `keyword` | `index.md` frontmatter | `stable` | `draft` / `stable` / `deprecated` |
| `language` | `keyword` | `index.md` frontmatter | `en` | `id` / `en` |
| `tags` | `keyword[]` | `index.md` frontmatter | `["auth","keycloak"]` | Tags untuk filtering |
| `checksum` | `keyword` | Auto (SHA-256 konten) | `a1b2c3d4...` | Untuk deteksi perubahan |
| `chunk_index` | `integer` | Auto (urutan chunk) | `0`, `1`, `2` | Urutan chunk dalam file |
| `chunk_text` | `text` | Auto (isi chunk) | `"## Installation\n..."` | Teks asli chunk (untuk display) |

---

## 7. Deployment

### 7.1 Docker Compose

```yaml
# docker-compose.yml (di repo agentix-context-library)

version: "3.8"

services:
  # ─── Vector Database (Persistent) ──────────────────
  qdrant:
    image: qdrant/qdrant:latest
    container_name: agentix-qdrant
    ports:
      - "6333:6333"    # REST API
      - "6334:6334"    # gRPC
    volumes:
      - qdrant-data:/qdrant/storage
    restart: unless-stopped

  # ─── MCP Server (Persistent) ───────────────────────
  mcp-server:
    build: ./engine/mcp-server
    container_name: agentix-mcp-server
    depends_on:
      - qdrant
    volumes:
      - ./context-registry:/data/context-registry:ro   # Read-only mount
    environment:
      - QDRANT_URL=http://qdrant:6333
      - CONTEXT_ROOT=/data/context-registry
      - EMBEDDING_MODEL=BAAI/bge-m3
    restart: unless-stopped

  # ─── Sync Engine (One-Shot, on-demand) ─────────────
  sync-engine:
    build: ./engine/sync-engine
    container_name: agentix-sync-engine
    depends_on:
      - qdrant
    volumes:
      - ./context-registry:/data/context-registry:ro   # Read-only mount
      - sync-venv:/app/venv                            # Persistent venv
    environment:
      - QDRANT_URL=http://qdrant:6333
      - CONTEXT_ROOT=/data/context-registry
      - EMBEDDING_MODEL=BAAI/bge-m3
    profiles:
      - sync    # Tidak berjalan saat `docker compose up`, hanya saat di-trigger

volumes:
  qdrant-data:
    driver: local
  sync-venv:
    driver: local
```

### 7.2 Cara Menjalankan

```bash
# 1. Start persistent services (Qdrant + MCP Server)
docker compose up -d

# 2. Jalankan sync (one-shot, on-demand)
docker compose run --rm sync-engine

# 3. Atau jalankan sync dengan profile
docker compose --profile sync run --rm sync-engine
```

### 7.3 GitLab Webhook Trigger (Tahap Lanjut)

```
GitLab Push Event
    │
    ▼
GitLab CI/CD Pipeline (.gitlab-ci.yml)
    │
    ▼
docker compose --profile sync run --rm sync-engine
    │
    ▼
Sync Report → GitLab Pipeline Output
```

---

## 8. Kapasitas & Estimasi

### 8.1 Skala Awal

| Metrik | Estimasi |
|---|---|
| Jumlah dokumen awal | ~50 files |
| Rata-rata chunks per dokumen | ~5-10 chunks |
| Total chunks awal | ~250-500 chunks |
| Pertumbuhan dokumen | ~2+ files/bulan |
| Concurrent agent queries | ~20+ agents |

### 8.2 Estimasi Resource

| Resource | Estimasi | Catatan |
|---|---|---|
| **Qdrant storage** | ~50 MB (500 vectors × 1024 dim × 4 bytes + metadata) | Sangat kecil untuk skala ini |
| **Qdrant memory** | ~256 MB-512 MB | Cukup untuk HNSW index 500 vectors |
| **BGE-M3 model size** | ~2.2 GB | Di-load saat sync dan MCP server startup |
| **Sync duration** | ~2-5 menit (50 docs) | Tergantung kecepatan embedding |
| **Query latency** | <100ms (Qdrant) + ~200ms (embedding) | Total ~300ms per query |

### 8.3 Proyeksi 1 Tahun

| Metrik | Bulan 0 | Bulan 6 | Bulan 12 |
|---|---|---|---|
| Dokumen | 50 | 62 | 74 |
| Chunks | 500 | 620 | 740 |
| Storage | 50 MB | 62 MB | 74 MB |

> ✅ Dengan skala ini, Qdrant single-node lebih dari cukup. Tidak perlu clustering hingga ratusan ribu vectors.

---

## 9. AI Agent Behavior

### 9.1 Strategi Eksplorasi (Folder-Aware)

AI Agent menggunakan 4 langkah untuk menemukan dan menggunakan konteks:

```
Step 1: SEMANTIC SEARCH
  └─ search_context(query) → top-k chunks paling relevan

Step 2: STATUS CHECK
  └─ Periksa status dari hasil:
     - stable → gunakan langsung
     - draft → gunakan, tapi klarifikasi ke user
     - deprecated → jangan gunakan

Step 3: CONTEXT EXPANSION
  └─ Dari hasil search, ambil directory_group
  └─ list_directory(directory_group) → lihat dokumen terkait
  └─ read_content(related_docs) → baca dokumen pendukung

Step 4: SYNTHESIZE & RESPOND
  └─ Gabungkan semua konteks
  └─ Hasilkan jawaban yang merujuk dokumen spesifik
  └─ Sertakan versi dan status dokumen
```

### 9.2 Contoh Interaksi Agent

```
User: "Bagaimana cara setup Keycloak untuk authentication?"

Agent:
  1. search_context("keycloak authentication setup")
     → Hasil: chunks dari backend/auth/keycloak-setup.md (score: 0.92)
     → Metadata: directory_group="backend/auth", status="stable", version="1.2.0"

  2. Status = stable → ✅ gunakan langsung

  3. list_directory("backend/auth")
     → Files: keycloak-setup.md, jwt-standard.md, oauth2-flow.md
     → Agent memutuskan membaca jwt-standard.md juga untuk konteks lengkap

  4. read_content("backend/auth/keycloak-setup.md")
     → Konten lengkap

  5. Response:
     "Berdasarkan dokumentasi Authentication Standards v1.2.0, 
      berikut cara setup Keycloak: ..."
```

---

## 10. Sync Policy

### 10.1 Aturan Upsert (Overwrite)

**Default Behavior: Skip Unchanged Files**

Sync Engine menggunakan checksum SHA-256 untuk mendeteksi perubahan.
File yang tidak berubah akan **di-skip** untuk menghemat resource.

| Kondisi | Aksi |
|---|---|
| File baru (belum ada di DB) | Chunk → Embed → Insert |
| File berubah (checksum berbeda) | Hapus chunks lama → Chunk ulang → Embed → Upsert |
| File tidak berubah (checksum sama) | **Skip (default)** atau Update (jika `--force`) |
| File dihapus dari filesystem | Hapus semua chunks dengan `path_document` tersebut |
| `status: deprecated` | Update metadata saja, chunks tetap ada |

**Force Sync Mode:**

Untuk force full re-sync (semua file di-update terlepas dari checksum):
```bash
docker compose --profile sync run --rm sync-engine --force
```

**Kapan menggunakan `--force`:**
- Setelah mengganti embedding model
- Setelah schema changes di Qdrant
- Untuk data migration atau recovery
- Untuk rebuild seluruh vector index

### 10.2 Konsistensi Model

> ⚠️ **KRITIS:** Embedding model yang digunakan Sync Engine dan MCP Server **HARUS IDENTIK**.
>
> Jika model diubah (misal: upgrade BGE-M3 ke versi baru), **SELURUH** data di Qdrant harus di-reindex (re-embed semua dokumen).

### 10.3 Sync Report Format

```
═══════════════════════════════════════
  Agentix Context Library — Sync Report
  Timestamp: 2026-02-15T00:15:00+07:00
═══════════════════════════════════════

  Source:    /data/context-registry
  Target:   http://qdrant:6333 (collection: context_library)
  Model:    BAAI/bge-m3

  Results:
  ├─ ✅ Added:   5 files  (28 chunks)
  ├─ 🔄 Updated: 3 files  (15 chunks)
  ├─ 🗑️  Deleted: 1 file   (6 chunks)
  ├─ ⏭️  Skipped: 41 files (unchanged)
  └─ ❌ Errors:  0 files

  Warnings:
  └─ ⚠️  backend/legacy/ — No index.md found, skipped

  Duration: 2m 34s
  Total chunks in DB: 487
═══════════════════════════════════════
```

---

## 11. Validasi & Error Handling

### 11.1 Validasi index.md

| Validasi | Aksi jika Gagal |
|---|---|
| `index.md` tidak ada di folder | WARNING, skip seluruh folder |
| Frontmatter tidak valid (YAML error) | ERROR, skip folder, log detail |
| `title` kosong/tidak ada | ERROR, skip folder |
| `version` bukan format SemVer | ERROR, skip folder |
| `status` bukan `draft`/`stable`/`deprecated` | ERROR, skip folder |
| `language` bukan `id`/`en` | ERROR, skip folder |

### 11.2 Validasi File .md

| Validasi | Aksi jika Gagal |
|---|---|
| File kosong | WARNING, skip file |
| File tidak bisa dibaca | ERROR, skip file, log detail |
| File bukan `.md` | Skip (bukan target) |

### 11.3 Error Handling Sync

| Skenario | Aksi |
|---|---|
| Qdrant tidak bisa dihubungi | EXIT dengan error, jangan proses apapun |
| BGE-M3 model gagal load | EXIT dengan error |
| Embedding gagal untuk 1 file | Log ERROR, lanjut ke file berikutnya |
| Partial sync (beberapa file gagal) | Log semua error, EXIT code 1 |
| Semua file sukses | EXIT code 0 |

---

## 12. Milestones Development

### Phase 1: Foundation (Prioritas Tertinggi)
- [ ] Setup Qdrant via Docker Compose
- [ ] Implementasi Sync Engine (Python)
  - [ ] Scanner & Validator (index.md parsing)
  - [ ] Chunking (recursive by headers)
  - [ ] Embedding (BGE-M3 integration)
  - [ ] Qdrant upsert & delete
  - [ ] Orphan detection & cleanup
  - [ ] Sync report output
- [ ] Buat sample dokumen di context-registry untuk testing
- [ ] Testing end-to-end: docs → sync → Qdrant → query manual

### Phase 2: MCP Server
- [ ] Implementasi MCP Server (Python)
  - [ ] Tool: `search_context`
  - [ ] Tool: `read_content`
  - [ ] Tool: `list_directory`
  - [ ] Tool: `get_metadata`
- [ ] Integrasi BGE-M3 untuk query embedding
- [ ] Testing dengan AI Agent

### Phase 3: Automation & Polish
- [ ] GitLab CI/CD pipeline untuk auto-trigger sync
- [ ] Monitoring & alerting (sync failures)
- [ ] Optimasi performa (caching, batch embedding)
- [ ] Dokumentasi deployment untuk tim

---

## 13. Referensi Dokumen Terkait

| Dokumen | Lokasi | Deskripsi |
|---|---|---|
| Ringkasan Arsitektur Awal | `docs/chat/history-14-feb-2026.md` | Diskusi arsitektur awal |
| User Stories | `docs/user-stories.md` | User stories & acceptance criteria |
| Contributor Guide | `docs/contributor-guide.md` | Panduan untuk contributor |
| index.md Template | `docs/templates/index-template.md` | Template frontmatter |
| Vector DB Specialist Skill | `.agent/skills/vector-db-specialist/SKILL.md` | Referensi best practices |
