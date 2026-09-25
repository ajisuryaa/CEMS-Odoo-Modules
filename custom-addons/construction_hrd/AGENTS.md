# AGENTS — `construction_hrd` (Phase 2)

Modul Site Workforce & Portal CEMS. Sebelum coding, baca:

**[document_project/pt_dynatech_batam/09_phase2_construction_hrd.md](../../document_project/pt_dynatech_batam/09_phase2_construction_hrd.md)**

Juga: [AGENTS.md pusat](../../document_project/pt_dynatech_batam/AGENTS.md) ·
[construction_progress/AGENTS.md](../construction_progress/AGENTS.md)

## Scope Phase 2

- Depends: `hr`, `hr_attendance`, `portal`, `website`, **`construction_progress`**
- Inherit `hr.employee` → tautkan ke `project.project`
- Portal check-in/out: GPS + selfie; **Haversine** vs geofence proyek (field dari Progress)
- `construction.daily.labor` (+ lines)
- `construction.gate.pass` (fondasi)
- Pakai `res.groups` CEMS dari `construction_progress` (jangan duplikasi group)

## Jangan kerjakan di Phase 2

- Daily Site Report / DSR → Phase 3 (`construction_progress`)
- Material request / stock → `construction_logistics`
- PTW / NCR → HSE / QC

## Aturan

1. Tidak modify core Odoo.
2. Validasi geofence **server-side** (bukan hanya JS).
3. Worker portal hanya lihat data sendiri (`employee_id.user_id = user`).
4. Geofence center/radius diambil dari `project.project` (Progress) — jangan redefinisi field.
