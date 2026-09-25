# 07 — Roadmap Development (Prioritas)

ERP bersifat hierarkis: material request butuh project yang sudah ada. **Jangan loncat fase.**

## Phase 1 — Core Foundation (Minggu 1–3)

**Target:** `construction_progress`  
**Landasan AI lengkap:** [08_phase1_construction_progress.md](./08_phase1_construction_progress.md)

1. Definisikan role internal (`res.groups`) di file security dasar.
2. Extend `project.project`: Geofence Radius, Center Lat/Long (+ BAC/EVM agregat).
3. Extend `project.task`: WBS, Weightage, EVM / physical progress.
4. Implement Record Rules untuk isolasi proyek (Project Manager / Site Engineer).

## Phase 2 — Site Workforce & Portal (Minggu 4–5)

**Target:** `construction_hrd`  
**Landasan AI lengkap:** [09_phase2_construction_hrd.md](./09_phase2_construction_hrd.md)

1. Extend `hr.employee` → tautkan worker ke `project.project`.
2. Controller Python: validasi Haversine geofence.
3. Portal web-app: HTML5 kamera + GPS.

## Phase 3 — Field Execution & Logistics (Minggu 6–8)

**Target:** `construction_progress` (bagian 2) + `construction_logistics`

1. Model `construction.daily.report` (DSR) → update progress fisik task.
2. Model `construction.material.request`.
3. State machine: approve MR → auto-create `stock.picking` (internal transfer).

## Phase 4 — Compliance & Quality (Minggu 9–11)

**Target:** `construction_engineering`, `construction_hse`, `construction_qc`

1. Documents app + status revisi konstruksi.
2. PTW + digital signature.
3. NCR: intercept `write` pada `project.task` — blok update progress jika NCR open.

## Phase 5 — Executive Analytics (Minggu 12–14)

**Target:** `construction_dashboard`

1. PostgreSQL view via model `_auto = False` (agregasi EVM, safety, inventory).
2. Komponen OWL frontend.
3. Chart.js / ApexCharts untuk S-Curve.

## Urutan install yang aman

```text
construction_progress
  → construction_hrd
  → construction_logistics
  → construction_engineering
  → construction_hse
  → construction_qc
  → construction_dashboard
```
