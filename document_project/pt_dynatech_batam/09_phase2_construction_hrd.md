# Phase 2 — Site Workforce: `construction_hrd`

**Landasan AI** Phase 2 CEMS (PT Dynatech Batam).  
Baca juga: [AGENTS.md](./AGENTS.md) · [07_roadmap.md](./07_roadmap.md) · [03_spesifikasi_fungsional.md](./03_spesifikasi_fungsional.md) §3.3 · [08_phase1_construction_progress.md](./08_phase1_construction_progress.md)

| Item | Nilai |
|------|--------|
| **Addon** | `construction_hrd` |
| **Path** | `custom-addons/construction_hrd/` |
| **Odoo** | **19 Community** |
| **Depends** | `hr`, `hr_attendance`, `mail`, `portal`, `website`, **`construction_progress`** |
| **Out of scope** | DSR, logistics MR, PTW/NCR |

---

## 1. Tujuan

1. Tautkan worker (`hr.employee`) ke proyek CEMS.
2. Absensi portal dengan **selfie + GPS**, validasi **Haversine** terhadap geofence proyek (field dari Progress).
3. Daily Labor Report (headcount per trade / hire type).
4. Fondasi Gate Pass.

---

## 2. Integrasi dengan `construction_progress`

| Dari Progress | Dipakai HRD untuk |
|---------------|-------------------|
| `project.geofence_latitude/longitude/radius` | Validasi jarak check-in |
| `cems_engineer_ids` | Record rules DLR / gate pass |
| `group_cems_*` | ACL & menu (tidak duplikasi group) |
| `menu_cems_root` | Parent menu **Site HRD** |

**Jangan** redefinisi field geofence di HRD.

---

## 3. Struktur folder

```text
custom-addons/construction_hrd/
├── __init__.py
├── __manifest__.py
├── AGENTS.md
├── README.md
├── controllers/
│   └── portal_attendance.py
├── models/
│   ├── hr_employee.py
│   ├── hr_attendance.py          # Haversine + portal check-in/out
│   ├── daily_labor.py
│   └── gate_pass.py
├── views/
│   ├── hr_employee_views.xml
│   ├── hr_attendance_views.xml
│   ├── daily_labor_views.xml
│   ├── gate_pass_views.xml
│   ├── menu_items.xml
│   └── portal_templates.xml
├── security/
│   ├── ir.model.access.csv
│   └── ir_rules.xml
├── data/
│   └── sequences.xml
└── static/src/
    ├── js/geolocation.js
    ├── css/portal_attendance.css
    └── img/attendance.svg
```

---

## 4. Deliverable checklist

- [x] Scaffold + depends `construction_progress`
- [x] `hr.employee`: `cems_project_id`, trade, hire type
- [x] Haversine server-side + portal check-in/out + selfie
- [x] `construction.daily.labor` (+ lines)
- [x] `construction.gate.pass`
- [x] ACL + ir.rule (engineer / manager / portal own)
- [x] Menu CEMS → Site HRD
- [x] Portal page `/my/cems/attendance`

---

## 5. Rumus geofence

\[
d = 2r \arcsin\sqrt{\sin^2\frac{\Delta\phi}{2}+\cos\phi_1\cos\phi_2\sin^2\frac{\Delta\lambda}{2}}
\]

\(r = 6{,}371{,}000\) m. Jika \(d >\) `geofence_radius` → `ValidationError`.

---

## 6. Cara uji cepat

1. Install `construction_progress` lalu `construction_hrd`.
2. Isi geofence proyek (titik dekat lokasi uji).
3. Employee: Related User = portal user; Site Project = proyek itu.
4. Login portal → Site Attendance → Check In.
5. Backend: Attendance menampilkan distance + selfie + Inside Geofence.

---

## 7. Setelah Phase 2

Lanjut [07_roadmap.md](./07_roadmap.md) Phase 3 — DSR + `construction_logistics`.
