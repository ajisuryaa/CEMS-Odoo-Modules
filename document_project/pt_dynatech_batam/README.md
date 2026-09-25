# PT Dynatech Batam — Acuan AI (CEMS)

Dokumen ini adalah **indeks acuan untuk AI/agent** agar memahami proyek **Odoo Construction & Engineering Management Suite (CEMS)** milik PT Dynatech Batam tanpa membaca file Word asli.

| File | Isi |
|------|-----|
| [AGENTS.md](./AGENTS.md) | Instruksi singkat wajib untuk AI saat mengerjakan proyek ini |
| [01_arsitektur.md](./01_arsitektur.md) | Ringkasan eksekutif & arsitektur sistem |
| [02_matriks_modul.md](./02_matriks_modul.md) | Dependensi modul custom vs Odoo core |
| [03_spesifikasi_fungsional.md](./03_spesifikasi_fungsional.md) | Fitur per domain + rumus bisnis |
| [04_struktur_direktori.md](./04_struktur_direktori.md) | Scaffold folder addon Odoo |
| [05_keamanan_rbac.md](./05_keamanan_rbac.md) | Grup, akses CRUD, record rules |
| [06_metodologi_dev.md](./06_metodologi_dev.md) | Aturan inheritance Python/XML |
| [07_roadmap.md](./07_roadmap.md) | Urutan fase development |
| [08_phase1_construction_progress.md](./08_phase1_construction_progress.md) | Landasan AI Phase 1 — modul `construction_progress` |
| [09_phase2_construction_hrd.md](./09_phase2_construction_hrd.md) | Landasan AI Phase 2 — modul `construction_hrd` |
| [README_construction_progress.md](./README_construction_progress.md) | **Panduan pengguna** — install, run, cara pakai `construction_progress` |

**Sumber:** `project PT.dynatech.docx` (SRS & Architecture Blueprint v1.1.0)  
**Target:** Odoo 19 Community  
**Lokasi kode target:** `custom_addons/` (atau `custom-addons/` di repo ini)

## Cara AI memakai dokumen ini

1. Baca `AGENTS.md` dulu (aturan keras).
2. Untuk Phase 1 Progress: wajib baca `08_phase1_construction_progress.md` (+ `custom-addons/construction_progress/AGENTS.md`).
3. Untuk Phase 2 HRD: wajib baca `09_phase2_construction_hrd.md` (+ `custom-addons/construction_hrd/AGENTS.md`); depends Progress.
4. Untuk fitur baru, cek `02_matriks_modul.md` + `03_spesifikasi_fungsional.md`.
5. Ikuti urutan `07_roadmap.md` — jangan loncat fase yang bergantung pada fondasi.
6. Semua kustomisasi hanya lewat `_inherit` / `<xpath>` — lihat `06_metodologi_dev.md`.

---

## Panduan pengguna — `construction_progress`

Untuk manusia (PM, engineer, admin Odoo): lihat **[README_construction_progress.md](./README_construction_progress.md)**.

Ringkas:

| Langkah | Perintah / aksi |
|---------|-----------------|
| Jalankan Odoo | `./odoo/odoo-bin -d cems_dev --addons-path=odoo/addons,odoo/odoo/addons,custom-addons` |
| Install modul | Apps → **CEMS Construction Progress**, atau `-i construction_progress` |
| Upgrade | `-u construction_progress --stop-after-init` |
| Pakai | **CEMS → Projects/Tasks** — isi geofence, WBS, BAC/PV; assign role CEMS di Users |

Ringkasan singkat juga ada di [`custom-addons/construction_progress/README.md`](../../custom-addons/construction_progress/README.md).

## Panduan pengguna — `construction_hrd`

| Langkah | Aksi |
|---------|------|
| Install | Setelah Progress: `-i construction_hrd` |
| Setup | Employee → CEMS / Site (project + related user); Project geofence terisi |
| Portal | `/my/cems/attendance` — GPS + selfie check-in |
| Backend | **CEMS → Site HRD** (DLR, Gate Pass, Attendances) |

Detail: [09_phase2_construction_hrd.md](./09_phase2_construction_hrd.md) · [`custom-addons/construction_hrd/README.md`](../../custom-addons/construction_hrd/README.md).
