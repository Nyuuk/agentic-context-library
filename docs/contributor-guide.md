# Contributor Guide — Context Registry

> Panduan lengkap untuk menambah, mengupdate, dan mengelola dokumen di **Context Registry**.
> Context Registry adalah sumber kebenaran (*Single Source of Truth*) yang digunakan AI Agent untuk memberikan jawaban yang konsisten dengan standar organisasi.

---

## Daftar Isi

1. [Konsep Dasar](#konsep-dasar)
2. [Struktur Folder](#struktur-folder)
3. [Format index.md](#format-indexmd)
4. [Menambahkan Topik Baru](#menambahkan-topik-baru)
5. [Menambahkan Dokumen ke Topik yang Ada](#menambahkan-dokumen-ke-topik-yang-ada)
6. [Mengupdate Dokumen](#mengupdate-dokumen)
7. [Menghapus Dokumen](#menghapus-dokumen)
8. [Versioning (SemVer)](#versioning-semver)
9. [Status Lifecycle](#status-lifecycle)
10. [Aturan dan Validasi](#aturan-dan-validasi)
11. [FAQ](#faq)

---

## Konsep Dasar

### Bagaimana Sistem Ini Bekerja

```
┌─────────────────────┐       ┌──────────────┐       ┌──────────────┐
│   Context Registry  │──────▶│  Sync Engine │──────▶│  Vector DB   │
│   (Git Repository)  │       │  (Chunking + │       │  (Semantic   │
│                     │       │   Embedding) │       │   Search)    │
│  Anda menulis       │       │              │       │              │
│  dokumen di sini    │       │  Otomatis    │       │  AI Agent    │
│                     │       │  memproses   │       │  mencari     │
│                     │       │  dokumen     │       │  dari sini   │
└─────────────────────┘       └──────────────┘       └──────────────┘
```

1. **Anda** menulis dokumen Markdown di Context Registry
2. **Sync Engine** otomatis memproses dokumen menjadi vektor
3. **AI Agent** mencari informasi dari Vector DB untuk menjawab pertanyaan

### Prinsip Utama

- **Satu folder = Satu topik** — Setiap folder mewakili satu topik/domain
- **`index.md` = Identitas folder** — Setiap folder HARUS punya `index.md` dengan metadata
- **File biasa = Frictionless** — File `.md` selain `index.md` TIDAK perlu frontmatter
- **Metadata diwarisi** — Semua file di folder otomatis mewarisi metadata dari `index.md`

---

## Struktur Folder

### Aturan Dasar

| Aturan | Deskripsi |
|---|---|
| Setiap folder HARUS punya `index.md` | Folder tanpa `index.md` akan di-skip oleh Sync Engine |
| File HARUS dalam folder | File `.md` langsung di root context-registry **tidak diizinkan** |
| Nested depth unlimited | Folder boleh nested sedalam apapun |
| Penamaan folder: lowercase + dash | Contoh: `backend-services/`, bukan `Backend Services/` |

### Contoh Struktur

```
context-registry/
│
├── backend/
│   ├── index.md                          ← Metadata untuk topik "backend"
│   ├── overview.md                       ← Konten biasa (tanpa frontmatter)
│   │
│   ├── auth/
│   │   ├── index.md                      ← Metadata untuk sub-topik "auth"
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
│           ├── index.md                  ← Folder nested tetap diproses
│           ├── ingress.md
│           └── service-mesh.md
│
└── policies/
    ├── index.md
    ├── naming-convention.md
    └── code-review.md
```

---

## Format index.md

### Template

```markdown
---
title: "Judul Topik"
version: "1.0.0"
status: stable
language: en
tags: [tag1, tag2, tag3]
---

# Judul Topik

Overview singkat tentang apa yang dicakup oleh folder/topik ini.

## Dokumen Terkait

- `file-satu.md` — Deskripsi singkat
- `file-dua.md` — Deskripsi singkat
```

### Field Frontmatter

| Field | Wajib | Tipe | Contoh | Deskripsi |
|---|---|---|---|---|
| `title` | ✅ Ya | string | `"Keycloak Authentication"` | Judul topik/folder |
| `version` | ✅ Ya | string (SemVer) | `"1.2.0"` | Versi dokumen, format `X.Y.Z` |
| `status` | ✅ Ya | enum | `stable` | Status: `draft`, `stable`, atau `deprecated` |
| `language` | ✅ Ya | enum | `en` | Bahasa: `id` (Indonesia) atau `en` (English) |
| `tags` | ❌ Opsional | array | `[auth, keycloak]` | Tag untuk filtering |

### Contoh Nyata

```markdown
---
title: "Kubernetes Cluster Standards"
version: "2.1.0"
status: stable
language: en
tags: [kubernetes, k8s, cluster, infrastructure]
---

# Kubernetes Cluster Standards

Dokumen ini mendefinisikan standar konfigurasi dan pengelolaan
Kubernetes cluster di organisasi.

## Dokumen di Folder Ini

- `cluster-setup.md` — Panduan setup cluster baru
- `helm-standards.md` — Standar penggunaan Helm charts
- `networking/` — Sub-topik tentang networking (lihat `networking/index.md`)
```

---

## Menambahkan Topik Baru

### Langkah-langkah

1. **Buat folder** di lokasi yang sesuai dalam hierarki:
   ```bash
   mkdir -p context-registry/backend/caching
   ```

2. **Buat `index.md`** dengan frontmatter:
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

   Standar dan panduan implementasi caching di backend services.

   ## Dokumen Terkait

   - `redis-setup.md` — Panduan setup Redis
   - `cache-invalidation.md` — Strategi invalidasi cache
   EOF
   ```

3. **Tambahkan file pendukung** (opsional):
   ```bash
   # File ini TIDAK perlu frontmatter
   cat > context-registry/backend/caching/redis-setup.md << 'EOF'
   # Redis Setup Guide

   ## Prerequisites

   - Redis 7.x atau lebih baru
   - Minimum 2GB RAM dedicated

   ## Installation

   ...konten...
   EOF
   ```

4. **Commit & push:**
   ```bash
   git add .
   git commit -m "feat: add caching strategy documentation"
   git push
   ```

5. **Jalankan Sync Engine** (manual):
   ```bash
   # Detail command akan ditentukan saat implementasi Sync Engine
   python sync.py --source /path/to/context-registry
   ```

---

## Menambahkan Dokumen ke Topik yang Ada

### Langkah-langkah

1. **Buat file `.md` baru** di folder yang sudah memiliki `index.md`:
   ```bash
   cat > context-registry/backend/auth/saml-integration.md << 'EOF'
   # SAML Integration Guide

   ## Overview

   Panduan integrasi SAML 2.0 untuk Single Sign-On.

   ## Configuration Steps

   1. Setup Identity Provider
   2. Configure Service Provider
   ...
   EOF
   ```

   > ⚠️ **TIDAK PERLU frontmatter!** File ini otomatis mewarisi metadata dari `backend/auth/index.md`.

2. **(Opsional) Update `index.md`** untuk mencantumkan file baru di daftar dokumen:
   ```markdown
   ## Dokumen Terkait
   
   - `keycloak-setup.md` — Setup Keycloak
   - `jwt-standard.md` — Standar JWT
   - `saml-integration.md` — Panduan integrasi SAML    ← TAMBAH INI
   ```

3. **Commit & push**, lalu jalankan Sync Engine.

---

## Mengupdate Dokumen

### Update Konten File Biasa

Cukup edit file, commit, dan push. Sync Engine akan mendeteksi perubahan checksum otomatis.

```bash
# Edit file
vim context-registry/backend/auth/keycloak-setup.md

# Commit
git commit -am "fix: update keycloak setup steps"
```

> 💡 **Tidak perlu mengubah `index.md`** untuk perubahan kecil pada file biasa.

### Update Metadata / Status di index.md

Gunakan ini saat ada perubahan signifikan pada topik secara keseluruhan:

```bash
# Edit index.md
vim context-registry/backend/auth/index.md
```

```yaml
---
title: "Authentication Standards"
version: "1.1.0"          # ← Bump version sesuai tingkat perubahan
status: stable
language: en
tags: [auth, keycloak, jwt, saml]    # ← Tambah tag baru jika perlu
---
```

> ⚠️ **Penting:** Saat `index.md` diupdate, Sync Engine akan memperbarui metadata untuk SEMUA file di folder tersebut.

---

## Menghapus Dokumen

### Metode 1: Soft Delete (Deprecated)

Gunakan untuk dokumen yang mungkin masih diperlukan sebagai referensi historis.

```yaml
# Di index.md, ubah status:
---
title: "Legacy Auth Method"
version: "1.3.0"
status: deprecated          # ← Ubah dari stable ke deprecated
language: en
tags: [auth, legacy]
---
```

> AI Agent akan **tidak menggunakan** dokumen deprecated, kecuali diminta secara eksplisit.

### Metode 2: Hard Delete

Gunakan untuk dokumen yang benar-benar tidak relevan lagi.

```bash
# Hapus satu file
rm context-registry/backend/auth/old-method.md

# Atau hapus seluruh folder/topik
rm -rf context-registry/backend/legacy-system/

# Commit & push
git commit -am "chore: remove legacy system documentation"
git push
```

Sync Engine akan menghapus semua chunks terkait dari Vector DB pada sync berikutnya.

---

## Versioning (SemVer)

Format: **`MAJOR.MINOR.PATCH`** (contoh: `2.1.3`)

| Perubahan | Level | Contoh | Kapan Digunakan |
|---|---|---|---|
| Restrukturisasi total | **MAJOR** | `1.0.0` → `2.0.0` | Ganti arsitektur, breaking change |
| Penambahan signifikan | **MINOR** | `2.0.0` → `2.1.0` | Tambah dokumen baru, fitur baru |
| Perbaikan kecil | **PATCH** | `2.1.0` → `2.1.1` | Fix typo, klarifikasi, minor update |

### Kapan Harus Bump Version?

- ✅ **Bump** saat ada perubahan signifikan pada topik
- ✅ **Bump** saat menambah/menghapus file di folder
- ✅ **Bump** saat mengubah tag atau status
- ❌ **Tidak perlu bump** jika hanya fix typo di satu file biasa (tapi boleh bump patch)

---

## Status Lifecycle

```
  ┌──────────┐         ┌──────────┐         ┌──────────────┐
  │  draft   │────────▶│  stable  │────────▶│  deprecated  │
  └──────────┘         └──────────┘         └──────────────┘
       │                     │
       │                     ▼
       │               (update konten,
       │                bump version,
       │                tetap stable)
       │
       └── Dokumen baru yang belum
           divalidasi/review
```

| Status | Sync ke DB? | Perilaku AI Agent |
|---|---|---|
| `draft` | ✅ Ya | Agent BOLEH menggunakan, tapi **WAJIB mengklarifikasi** bahwa ini dokumen draft |
| `stable` | ✅ Ya | Agent menggunakan sebagai **referensi utama** |
| `deprecated` | ✅ Ya | Agent **TIDAK menggunakan**, kecuali diminta eksplisit oleh user |

---

## Aturan dan Validasi

### ✅ Yang HARUS Dilakukan

- Setiap folder HARUS memiliki `index.md` dengan frontmatter valid
- Gunakan penamaan folder: **lowercase, dash-separated** (`my-topic/`)
- Gunakan penamaan file: **lowercase, dash-separated** (`my-document.md`)
- Tulis konten yang jelas dan terstruktur menggunakan heading Markdown
- Bump version di `index.md` saat ada perubahan signifikan

### ❌ Yang TIDAK BOLEH Dilakukan

- Menaruh file `.md` langsung di root `context-registry/` tanpa folder
- Membuat folder tanpa `index.md`
- Menambahkan frontmatter di file selain `index.md`
- Menggunakan `version` yang tidak mengikuti format SemVer (`X.Y.Z`)
- Menggunakan `status` selain `draft`, `stable`, atau `deprecated`

---

## FAQ

### Q: Apakah saya perlu frontmatter di setiap file?
**A:** Tidak. Frontmatter hanya diperlukan di `index.md`. File `.md` biasa tidak memerlukan frontmatter.

### Q: Bagaimana jika saya lupa membuat `index.md`?
**A:** Sync Engine akan SKIP folder tersebut dan memberikan warning. Semua file di folder itu tidak akan diproses hingga `index.md` dibuat.

### Q: Apakah AI Agent bisa menemukan dokumen `draft`?
**A:** Ya, tapi agent akan memberikan klarifikasi kepada user bahwa dokumen tersebut masih berstatus draft dan belum divalidasi.

### Q: Bagaimana jika saya memindahkan file ke folder lain?
**A:** Sync Engine akan mendeteksi ini sebagai: (1) file baru di folder tujuan, dan (2) file hilang di folder asal. Chunks lama dihapus, chunks baru dibuat dengan metadata folder tujuan.

### Q: File format apa saja yang didukung?
**A:** Saat ini hanya file **Markdown (`.md`)** yang didukung.
