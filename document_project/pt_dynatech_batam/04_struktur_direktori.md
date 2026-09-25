# 04 — Struktur Direktori Addon

Ikuti scaffolding Odoo standar. Contoh struktur inti:

```text
custom_addons/
├── construction_progress/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── project_project.py        # Geofence lat/long/radius
│   │   ├── project_task.py           # WBS + EVM
│   │   └── daily_site_report.py      # Model DSR baru
│   ├── views/
│   │   ├── project_views_inherit.xml # XPath inject form task/project
│   │   ├── daily_report_views.xml    # Form, list, kanban DSR
│   │   └── menu_items.xml
│   └── security/
│       ├── ir.model.access.csv
│       └── ir_rules.xml              # Isolasi multi-project
│
├── construction_hrd/
│   ├── controllers/
│   │   └── portal_attendance.py      # POST GPS + foto Base64
│   ├── static/src/
│   │   ├── js/geolocation.js
│   │   └── xml/camera_widget.xml
│   └── views/
│       └── portal_templates.xml
│
└── construction_dashboard/
    ├── static/src/
    │   └── components/               # OWL (Odoo 19)
    │       ├── dashboard.js
    │       ├── dashboard.xml
    │       └── chart_widget.js       # Chart.js / ApexCharts
    └── models/
        └── kpi_sql_view.py           # tools.drop_view_if_exists + _auto=False
```

## Konvensi untuk AI

| Area | Lokasi |
|------|--------|
| Model / business logic | `models/*.py` |
| UI backend | `views/*.xml` |
| Portal / HTTP | `controllers/` + `views/*_templates.xml` |
| JS/OWL/CSS | `static/src/` |
| Hak akses | `security/ir.model.access.csv` + `ir_rules.xml` |
| Data awal / demo | `data/` (jika ada) |

Addon lain (`construction_engineering`, `construction_logistics`, `construction_hse`, `construction_qc`) mengikuti pola folder yang sama.
