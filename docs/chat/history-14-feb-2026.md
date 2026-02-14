## **Ringkasan Arsitektur: Agentic Context Library**

Sistem ini dirancang untuk menciptakan **Single Source of Truth** bagi AI Agent agar output yang dihasilkan konsisten dengan standar organisasi melalui mekanisme **Agentic RAG**.

### **1. Komponen Utama**

* **Context Registry:** Repository berisi dokumen Markdown terstruktur yang menjadi acuan utama.
* **Sync Engine:** Pipeline otomatis untuk memproses dokumen (chunking, hashing, embedding) dan memperbarui database secara berkala.
* **Vector Database:** Penyimpanan terpusat untuk pencarian semantik berdasarkan vektor teks.
* **MCP Server:** Antarmuka komunikasi yang memungkinkan AI Agent mencari dan membaca dokumen secara mendalam.

---

### **2. Skema Metadata Terintegrasi**

Setiap potongan data (*chunk*) di database wajib membawa metadata berikut untuk mendukung navigasi AI:

| Metadata Field | Fungsi Utama |
| --- | --- |
| **`document_id`** | Hash unik (`path` + `index`) untuk mencegah duplikasi data (Upsert). |
| **`path_document`** | Jalur lengkap file (misal: `/backend/auth/keycloak.md`) sebagai kunci navigasi. |
| **`directory_group`** | Nama folder induk untuk pengelompokan konteks yang terkait. |
| **`version`** | Penanda versi dokumen (contoh: `1.0.0`). |
| **`status`** | Status validitas dokumen (misal: `stable`, `deprecated`). |
| **`checksum`** | Hash isi konten untuk mendeteksi perubahan sebelum update. |

---

### **3. Strategi Eksplorasi Agent (Folder-Aware)**

AI Agent tidak hanya melakukan pencarian kata kunci, melainkan menggunakan logika navigasi:

1. **Semantic Retrieval:** Menemukan potongan informasi paling relevan.
2. **Path Analysis:** Membaca metadata `path_document` dari hasil tersebut.
3. **Context Expansion:** Agent secara mandiri mencari dokumen lain di dalam folder/direktori yang sama untuk melengkapi pemahaman (misal: mencari file konfigurasi di folder yang sama dengan file instruksi).
4. **Final Implementation:** Menghasilkan output berdasarkan gabungan konteks yang telah divalidasi.

---

### **4. Aturan Pembaruan Data (Sync Policy)**

* **Update:** Jika isi file berubah, sistem melakukan *overwrite* (Upsert) berdasarkan `document_id`.
* **Deletion:** Jika file dihapus dari sumber, sistem menghapus semua baris di database yang memiliki `path_document` tersebut.
* **Consistency:** Model embedding yang digunakan untuk sinkronisasi data harus identik dengan model yang digunakan Agent saat melakukan pencarian.

---

## **Langkah Development Selanjutnya**

* Penyusunan format baku Markdown (Frontmatter) agar seragam.
* Pembuatan script otomatisasi untuk proses `Teks -> Embedding -> Vector DB`.
* Pembuatan MCP Server dengan fungsi `search_context` (filter by path) dan `read_content`.
* Penyusunan instruksi (System Prompt) agar AI Agent aktif melakukan eksplorasi berdasarkan jalur dokumen.