# CEMS Construction Progress

User guide for **`construction_progress`** — Phase 1 foundation of the Construction & Engineering Management Suite (CEMS) for PT Dynatech Batam.

| | |
|---|---|
| **Technical name** | `construction_progress` |
| **Version** | `19.0.1.0.0` |
| **Category** | Construction |
| **Depends on** | `project`, `hr_timesheet` |
| **Compatible with** | Odoo **19.0 Community** |
| **License** | LGPL-3 |

Full how-to (install, roles, WBS, EVM):  
**[document_project/pt_dynatech_batam/README_construction_progress.md](../../document_project/pt_dynatech_batam/README_construction_progress.md)**

Developer / AI landasan:  
[08_phase1_construction_progress.md](../../document_project/pt_dynatech_batam/08_phase1_construction_progress.md) · [AGENTS.md](./AGENTS.md)

---

## Features (Phase 1)

- CEMS **security groups** (Director, Manager, Site Engineer, HSE, QC, …)
- Project **geofence** (latitude, longitude, radius)
- Task **WBS code**, **weightage**, **physical progress**
- Project **EVM**: BAC, PV, \(P_{total}\), EV, SPI
- **Record rules** isolating Site Engineers via `cems_engineer_ids`

Out of scope here: Daily Site Report, portal GPS, material request (later phases).

---

## Quick start

From `pmg-odoo/` with venv active and PostgreSQL running:

```bash
# Start (example)
./odoo/odoo-bin -d cems_dev \
  --addons-path=odoo/addons,odoo/odoo/addons,custom-addons

# Install
./odoo/odoo-bin -d cems_dev \
  --addons-path=odoo/addons,odoo/odoo/addons,custom-addons \
  -i construction_progress --stop-after-init

# Upgrade after code changes
./odoo/odoo-bin -d cems_dev \
  --addons-path=odoo/addons,odoo/odoo/addons,custom-addons \
  -u construction_progress --stop-after-init
```

Then open [http://localhost:8069](http://localhost:8069) → **Apps** → install **CEMS Construction Progress** (if not installed via CLI).

Ensure `custom-addons` (parent of this folder) is listed in `addons_path`.

---

## Currency

EVM amounts (BAC / PV / EV) use **company currency**. First install activates **IDR (Rp)** for the main company. To set it manually: **Settings → Companies → Currency = IDR** (activate IDR under **Settings → Currencies** if needed).

## How to use (short)

1. **Settings → Users** — assign a **CEMS** group (e.g. Project Manager, Site Engineer).
2. **CEMS → Projects** — set geofence, BAC/PV, **Site Engineers**, optionally **WBS Validated**.
3. **CEMS → Tasks** — fill WBS code, weightage (%), physical progress (%).
4. Open the project **Progress & EVM** tab to read \(P_{total}\), EV, SPI.

Weightages of billable tasks should sum to **100%** before you tick **WBS Validated**.

---

## Project structure

```text
construction_progress/
├── __init__.py
├── __manifest__.py
├── AGENTS.md
├── models/
│   ├── project_project.py
│   └── project_task.py
├── views/
│   ├── project_views_inherit.xml
│   ├── project_task_views_inherit.xml
│   └── menu_items.xml
├── security/
│   ├── cems_groups.xml
│   ├── ir.model.access.csv
│   └── ir_rules.xml
└── data/
```

---

## Troubleshooting

| Problem | Check |
|---------|--------|
| Module missing in Apps | `addons_path` + Update Apps List + restart |
| Fields not on form | `-u construction_progress` |
| Engineer sees no projects | Add user to project **Site Engineers** |
| SPI = 0 | Set **PV** &gt; 0 and BAC / task progress |

See the [full user guide](../../document_project/pt_dynatech_batam/README_construction_progress.md) for details.
