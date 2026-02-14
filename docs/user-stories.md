# User Stories — Agentix Context Library

> **Dokumen ini adalah hasil diskusi dan kesepakatan pada 14 Februari 2026.**
> Menjadi acuan utama untuk pengembangan fitur dan pembuatan guideline.

---

## Persona

| Persona | Deskripsi |
|---|---|
| **Contributor** | DevOps Engineer / Engineer yang menulis & mengelola dokumen di `context-registry` |
| **Sync Engine** | Pipeline otomatis yang memproses dokumen menjadi vektor |
| **AI Agent** | AI yang membaca konteks dari Vector DB via MCP Server |

---

## Keputusan Arsitektur yang Disepakati

| Aspek | Keputusan | Detail |
|---|---|---|
| **Frontmatter** | Hanya di `index.md` | File `.md` biasa TIDAK perlu frontmatter, metadata diwarisi dari `index.md` parent |
| **Context Registry** | Git repo terpisah | Di-mount ke engine saat sync. Path relatif terhadap root `context-registry/` |
| **Trigger Sync** | Manual → Docker | Tahap awal manual, lalu via Docker Python dengan mounting venv + context-registry |
| **Delete Strategy** | Soft + Hard | Soft delete via `status: deprecated`, hard delete via hapus file dari repo |
| **Versioning** | Manual (SemVer) | Format `X.Y.Z` — Major.Minor.Patch. Contributor bertanggung jawab bump version |
| **Bahasa** | Indonesia + Inggris | Memerlukan embedding model multilingual. Flag `language` di frontmatter |
| **index.md konten** | Boleh berisi konten lengkap | index.md boleh hanya metadata + overview, atau berisi konten substantif |
| **Nested folder** | Unlimited depth | Folder boleh nested sedalam apapun, selama ada `index.md` |
| **File tanpa folder** | Tidak diizinkan | Semua file HARUS berada dalam folder yang memiliki `index.md` |
| **Draft status** | Tetap di-sync | Dokumen draft tetap masuk Vector DB, agent yang akan mengklarifikasi ke user |
| **DB Versioning** | Overwrite (hanya versi terbaru) | Git sebagai version history, Vector DB hanya menyimpan snapshot terkini |
| **Vector Database** | Qdrant (Docker) | Self-hosted, metadata filtering kuat, gratis, REST + gRPC API |
| **Embedding Model** | BGE-M3 (self-hosted) | Multilingual (ID+EN), open-source, 1024 dimensi |
| **Chunking** | Recursive by Markdown headers | Fallback ke fixed-size 512 tokens jika section terlalu panjang |
| **MCP Tools** | 4 tools | `search_context`, `read_content`, `list_directory`, `get_metadata` |
| **Deployment** | Docker Compose | Qdrant + MCP Server persisten, Sync Engine one-shot on-demand |
| **Sync Engine** | One-shot script | Bukan long-running service, di-trigger manual atau GitLab webhook |

---

## Epic 1: Manajemen Dokumen (Contributor Workflow)

### US-1.1: Menambahkan Topik/Folder Baru

> *Sebagai **Contributor**, saya ingin menambahkan topik baru ke context-registry dengan membuat folder + `index.md`, sehingga AI Agent bisa menggunakan informasi tersebut.*

**Alur:**
1. Buat folder baru di `context-registry/` sesuai hierarki yang logis
2. Buat `index.md` di dalam folder tersebut dengan frontmatter wajib
3. (Opsional) Tambahkan file `.md` pendukung di folder yang sama
4. Commit & push ke repo `context-registry`
5. Jalankan Sync Engine → semua file di folder baru diproses

**Acceptance Criteria:**
- [ ] Folder tanpa `index.md` → di-SKIP oleh Sync Engine dengan warning
- [ ] `index.md` dengan frontmatter valid → semua file di folder diproses
- [ ] `index.md` tanpa frontmatter / frontmatter invalid → ERROR dengan pesan jelas
- [ ] Metadata `document_id`, `path_document`, `directory_group` terisi otomatis dari path
- [ ] Setelah sync, dokumen bisa ditemukan oleh AI Agent via semantic search

---

### US-1.2: Menambahkan Dokumen ke Topik yang Sudah Ada

> *Sebagai **Contributor**, saya ingin menambahkan dokumen baru ke folder yang sudah ada, tanpa perlu mengurus frontmatter, sehingga proses kontribusi cepat dan mudah.*

**Alur:**
1. Buat file `.md` baru di folder yang sudah memiliki `index.md`
2. Tulis konten biasa (TANPA frontmatter)
3. Commit & push
4. Jalankan Sync Engine → file baru mewarisi metadata dari `index.md` parent

**Acceptance Criteria:**
- [ ] File `.md` biasa di folder yang punya `index.md` → diproses tanpa error
- [ ] Metadata `version`, `status`, `tags`, `language` diwarisi dari `index.md`
- [ ] `path_document` dan `document_id` tetap unik per file

---

### US-1.3: Mengupdate Dokumen

> *Sebagai **Contributor**, saya ingin mengupdate isi dokumen yang sudah ada, sehingga AI Agent selalu mendapat informasi terbaru.*

**Alur Update Konten Biasa:**
1. Edit file `.md` yang sudah ada
2. Commit & push
3. Jalankan Sync Engine:
   - Checksum dibandingkan → jika berbeda, re-chunk & re-embed
   - Upsert berdasarkan `document_id` (overwrite, bukan duplikasi)

**Alur Update Metadata / Status:**
1. Edit `index.md` di folder terkait
2. Ubah field yang diperlukan (version, status, tags, dll)
3. Commit & push
4. Jalankan Sync Engine → semua file di folder tersebut diupdate metadatanya

**Versioning Rules (SemVer: X.Y.Z):**

| Perubahan | Contoh | Bump |
|---|---|---|
| Restrukturisasi total, breaking change | Ganti arsitektur auth dari Keycloak ke Auth0 | **Major**: `1.0.0` → `2.0.0` |
| Penambahan fitur/dokumen signifikan | Tambah panduan SAML integration | **Minor**: `2.0.0` → `2.1.0` |
| Typo fix, klarifikasi kecil, update minor | Fix typo di langkah instalasi | **Patch**: `2.1.0` → `2.1.1` |

**Status Lifecycle:**

```
  draft ──────→ stable ──────→ deprecated
    │              │
    │              ▼
    │         (update konten,
    │          bump version)
    │
    └── Dokumen baru, belum divalidasi.
        Agent tetap bisa menemukan, tapi akan
        mengklarifikasi bahwa ini masih draft.
```

| Status | Deskripsi | Behavior Agent |
|---|---|---|
| `draft` | Dokumen baru, belum divalidasi/review | Agent BOLEH menggunakan, tapi WAJIB memberikan klarifikasi bahwa dokumen masih draft |
| `stable` | Dokumen sudah divalidasi, siap digunakan | Agent menggunakan sebagai referensi utama |
| `deprecated` | Dokumen sudah tidak relevan | Agent TIDAK menggunakan, kecuali diminta secara eksplisit |

**Acceptance Criteria:**
- [ ] Hanya file yang checksum-nya berubah yang di-reprocess
- [ ] Update `index.md` → propagasi metadata ke semua file di folder
- [ ] Chunk lama di-replace (bukan ditambah) saat upsert

---

### US-1.4: Menghapus Dokumen

> *Sebagai **Contributor**, saya ingin menghapus dokumen yang tidak relevan melalui soft delete atau hard delete.*

**Soft Delete (via status):**
1. Ubah `status: deprecated` di `index.md`
2. Commit & push
3. Sync Engine update metadata semua chunk di folder → agent memfilter

**Hard Delete (via file removal):**
1. Hapus file atau seluruh folder dari filesystem
2. Commit & push
3. Sync Engine membandingkan path di DB vs filesystem
4. Path yang ada di DB tapi TIDAK di filesystem → HAPUS dari Vector DB

**Acceptance Criteria:**
- [ ] Soft delete: metadata di Vector DB diupdate, chunks tetap ada
- [ ] Hard delete: semua chunks terkait path yang dihapus di-remove dari Vector DB
- [ ] Tidak ada orphan chunks setelah sync
- [ ] Output sync menunjukkan jumlah deleted chunks

---

### US-1.5: Mengorganisasi Dokumen dalam Folder

> *Sebagai **Contributor**, saya ingin mengorganisasi dokumen dalam struktur folder yang logis dan nested, sehingga AI Agent bisa melakukan context expansion berdasarkan `directory_group`.*

**Aturan:**
- Setiap folder HARUS memiliki `index.md`
- Nested depth: **unlimited**
- File tanpa folder (di root context-registry) **TIDAK diizinkan**
- `directory_group` otomatis diambil dari path relatif folder

**Contoh:**
```
context-registry/
├── backend/
│   ├── index.md                          # directory_group: "backend"
│   ├── auth/
│   │   ├── index.md                      # directory_group: "backend/auth"
│   │   ├── keycloak-setup.md
│   │   └── jwt-standard.md
│   └── database/
│       ├── index.md                      # directory_group: "backend/database"
│       └── postgresql.md
├── infrastructure/
│   ├── index.md                          # directory_group: "infrastructure"
│   └── kubernetes/
│       ├── index.md                      # directory_group: "infrastructure/kubernetes"
│       ├── cluster-setup.md
│       └── networking/
│           ├── index.md                  # directory_group: "infrastructure/kubernetes/networking"
│           ├── ingress.md
│           └── service-mesh.md
└── policies/
    ├── index.md                          # directory_group: "policies"
    ├── naming-convention.md
    └── code-review.md
```

**Acceptance Criteria:**
- [ ] `directory_group` digenerate otomatis dari path folder relatif terhadap root context-registry
- [ ] AI Agent bisa query berdasarkan `directory_group`
- [ ] Nested folder sedalam apapun tetap diproses

---

## Epic 2: Sync Engine (System Workflow)

### US-2.1: Sinkronisasi Manual

> *Sebagai **System**, saya ingin mensinkronkan perubahan di context-registry ke Vector DB secara manual, sehingga data selalu up-to-date.*

**Alur:**
1. Trigger: Jalankan script sync secara manual
2. Scan seluruh folder di context-registry
3. Untuk setiap folder yang memiliki `index.md`:
   a. Baca & validasi frontmatter `index.md`
   b. Scan semua file `.md` di folder (termasuk `index.md` itu sendiri)
   c. Untuk setiap file:
      - Hitung checksum konten
      - Bandingkan dengan checksum di Vector DB
      - Jika baru/berubah → chunk → embed → upsert (dengan metadata dari index.md)
      - Jika sama → skip
4. Cari orphan paths (ada di DB tapi tidak di filesystem) → hapus
5. Output: laporan sync (added, updated, deleted, skipped, errors)

**Deployment (tahap lanjut):**
```
Docker Python container dengan:
- Mounting venv (persistent dependencies)
- Mounting context-registry repo (read-only)
- Environment variables untuk Vector DB connection
```

---

### US-2.2: Validasi Dokumen

> *Sebagai **System**, saya ingin memvalidasi format dokumen sebelum memproses, sehingga data di Vector DB selalu berkualitas.*

**Validasi `index.md`:**
- [ ] File harus ada di setiap folder yang berisi `.md` files
- [ ] Frontmatter YAML harus valid
- [ ] Field wajib: `title`, `version`, `status`, `language`
- [ ] `version` harus format SemVer: `X.Y.Z`
- [ ] `status` harus salah satu: `draft`, `stable`, `deprecated`
- [ ] `language` harus salah satu: `id`, `en`

**Validasi file `.md` biasa:**
- [ ] File tidak boleh kosong
- [ ] File harus berada di folder yang memiliki `index.md` yang valid

---

## Epic 3: AI Agent Consumption (Consumer Workflow)

### US-3.1: Pencarian Konteks Semantik

> *Sebagai **AI Agent**, saya ingin mencari dokumen relevan berdasarkan query, dengan memperhatikan status dokumen.*

**Alur:**
1. Agent menerima query
2. Agent memanggil MCP tool: `search_context(query, filters?)`
3. MCP Server: embed query → vector search → return top-k chunks + metadata
4. Agent memeriksa `status` dari hasil:
   - `stable` → gunakan langsung
   - `draft` → gunakan, tapi beri klarifikasi ke user
   - `deprecated` → jangan gunakan, kecuali diminta eksplisit
5. Agent menganalisis `path_document` → lakukan context expansion jika perlu

### US-3.2: Context Expansion (Folder-Aware)

> *Sebagai **AI Agent**, saya ingin memperluas konteks dengan mencari dokumen lain di folder yang sama.*

**Alur:**
1. Dari hasil search, agent mendapat `directory_group`
2. Agent memanggil: `search_context(filter: directory_group = "backend/auth")`
3. Agent mendapat semua chunks dari folder terkait
4. Agent menyusun jawaban berdasarkan konteks gabungan

### US-3.3: Membaca Dokumen Lengkap

> *Sebagai **AI Agent**, saya ingin membaca isi lengkap suatu dokumen.*

**Alur:**
1. Dari hasil search, agent mendapat `path_document`
2. Agent memanggil: `read_content(path_document)`
3. MCP Server membaca file asli dari context-registry mount
4. Return konten lengkap dalam Markdown

---

## Metadata Schema (Final)

Setiap chunk di Vector DB memiliki metadata berikut:

| Field | Sumber | Contoh | Deskripsi |
|---|---|---|---|
| `document_id` | Auto-generated | `hash(path + chunk_index)` | Primary key untuk upsert |
| `path_document` | Auto dari filepath | `backend/auth/keycloak.md` | Path relatif terhadap root context-registry |
| `directory_group` | Auto dari folder path | `backend/auth` | Path folder untuk context expansion |
| `title` | Dari `index.md` frontmatter | `Authentication Standards` | Judul topik |
| `version` | Dari `index.md` frontmatter | `1.2.0` | Versi SemVer |
| `status` | Dari `index.md` frontmatter | `stable` | Status dokumen: draft / stable / deprecated |
| `language` | Dari `index.md` frontmatter | `en` | Bahasa dokumen: id / en |
| `tags` | Dari `index.md` frontmatter | `[auth, keycloak]` | Tag untuk filtering tambahan |
| `checksum` | Auto dari konten file | `sha256:abc123...` | Untuk deteksi perubahan |
| `chunk_index` | Auto dari chunking | `0`, `1`, `2` | Urutan chunk dalam file |
| `source_file` | Auto dari filename | `keycloak.md` | Nama file asal (tanpa path) |
