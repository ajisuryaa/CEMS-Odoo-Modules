# 02 — Matriks Modul & Dependensi

Deklarasikan `depends` di `__manifest__.py` sesuai kolom **Odoo Core Dependencies**. Jangan install addon custom tanpa dependensi inti — mencegah error relasi DB.

| Domain | Dependensi Odoo Core | Nama Addon Custom | Model kunci (`_name` / `_inherit`) |
|--------|----------------------|-------------------|-------------------------------------|
| 1. Engineering | `documents`, `mail` | `construction_engineering` | `construction.drawing`, `construction.transmittal`, `construction.rfi.tech` |
| 2. Progress & WBS | `project`, `hr_timesheet` | `construction_progress` | `project.project`, `project.task`, `construction.daily.report`, `construction.wbs` |
| 3. Site Logistics | `stock`, `purchase`, `fleet` | `construction_logistics` | `construction.material.request`, `fleet.vehicle`, `stock.picking` |
| 4. Site HRD | `hr`, `hr_attendance`, **`construction_progress`**, `portal`, `website` | `construction_hrd` | `construction.daily.labor`, `construction.gate.pass`, `hr.attendance`, `hr.employee` |
| 5. HSE (Safety) | `hr`, `construction_progress` | `construction_hse` | `construction.permit.work`, `construction.incident`, `construction.jsa` |
| 6. QC (Quality) | `project`, `construction_engineering` | `construction_qc` | `construction.inspection.request`, `construction.ncr`, `construction.punchlist` |
| 7. Dashboard | Semua di atas | `construction_dashboard` | `construction.kpi.view` (SQL auto-view), komponen OWL |

## Catatan untuk AI

- `construction_hse` bergantung pada `construction_progress` (bukan hanya `hr`).
- `construction_qc` bergantung pada `construction_engineering`.
- `construction_dashboard` harus di-`depends` ke semua addon domain agar aman saat install.
- Module install order mengikuti dependensi: **progress → hrd / logistics / engineering → hse / qc → dashboard**.
