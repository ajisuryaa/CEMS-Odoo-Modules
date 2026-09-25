# AGENTS — PT Dynatech Batam (CEMS)

Baca file ini sebelum mengubah/membuat kode terkait proyek construction Odoo PT Dynatech Batam.

## Identitas proyek

- **Nama produk:** Odoo Construction & Engineering Management Suite (**CEMS**)
- **Klien / konteks:** PT Dynatech Batam
- **Framework:** Odoo 19 Community
- **Pola:** Custom addon di atas native Odoo — **jangan ubah core Odoo**

## Tujuh addon domain

| Addon | Domain |
|-------|--------|
| `construction_progress` | WBS, progress fisik, EVM, daily site report |
| `construction_engineering` | Drawing, transmittal, RFI, revisi dokumen |
| `construction_logistics` | Material request, fleet, stock picking site |
| `construction_hrd` | Daily labor, gate pass, geofence attendance portal |
| `construction_hse` | Permit to Work, incident, JSA |
| `construction_qc` | Inspection, NCR, punchlist |
| `construction_dashboard` | KPI SQL view + OWL dashboard |

## Aturan keras untuk AI

1. **Never modify** file di `odoo/addons` / core Odoo.
2. Semua perubahan: `_inherit` (Python) + `<xpath>` (XML view inherit).
3. Deklarasikan `depends` di `__manifest__.py` sesuai [02_matriks_modul.md](./02_matriks_modul.md).
4. Isolasi data antar proyek via `ir.rule` — lihat [05_keamanan_rbac.md](./05_keamanan_rbac.md).
5. Ikuti urutan roadmap: Progress → HRD → Logistics → Engineering/HSE/QC → Dashboard.
6. Model naming: prefix `construction.*` untuk model baru; extend `project.*`, `stock.*`, `hr.*`, `fleet.*` bila perlu.

## Referensi cepat

- Arsitektur: [01_arsitektur.md](./01_arsitektur.md)
- Rumus progress/EVM/geofence/LTIFR: [03_spesifikasi_fungsional.md](./03_spesifikasi_fungsional.md)
- Struktur folder: [04_struktur_direktori.md](./04_struktur_direktori.md)
- **Phase 1 Progress:** [08_phase1_construction_progress.md](./08_phase1_construction_progress.md)
- **Phase 2 HRD:** [09_phase2_construction_hrd.md](./09_phase2_construction_hrd.md)
