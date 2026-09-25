# CEMS Construction Progress — User Guide

User-facing guide for the **`construction_progress`** module (Phase 1 foundation of CEMS — PT Dynatech Batam).

| | |
|---|---|
| **Technical name** | `construction_progress` |
| **Version** | `19.0.1.0.0` |
| **Odoo** | **19 Community** |
| **Depends on** | `project`, `hr_timesheet` |
| **Code path** | `custom-addons/construction_progress/` |
| **AI / developer landasan** | [08_phase1_construction_progress.md](./08_phase1_construction_progress.md) |

> For AI coding rules see [AGENTS.md](./AGENTS.md). This README is for **humans**: install, run, and day-to-day use.

---

## What this module does

`construction_progress` is the **first CEMS addon**. After install you get:

1. **CEMS security groups** (Director, Project Manager, Site Engineer, HSE, QC, …)
2. **Geofence** fields on each project (lat / long / radius) — used later by HRD attendance
3. **WBS + weightage + physical progress** on tasks
4. **EVM** on the project: BAC, PV, \(P_{total}\), EV, SPI
5. **Record rules** so Site Engineers only see assigned projects

**Not in Phase 1:** Daily Site Report (DSR), portal GPS, material request — those come in later phases.

---

## Requirements

1. Odoo **19** source (this repo: `pmg-odoo/odoo/`)
2. Python **3.10+** with a virtualenv (`pmg-odoo/venv/`)
3. PostgreSQL running
4. Odoo Python deps installed from `odoo/requirements.txt`
5. Apps **Project** and **Timesheets** available (installed automatically via depends)

Typical layout:

```text
pmg-odoo/
├── odoo/                          # Odoo 19 source
├── custom-addons/
│   └── construction_progress/     # this module
├── document_project/
│   └── pt_dynatech_batam/         # docs (this file)
└── venv/
```

---

## How to run / install

### 1. Activate venv & install Odoo deps (once)

```bash
cd /path/to/pmg-odoo
python3 -m venv venv
source venv/bin/activate
pip install -r odoo/requirements.txt
```

### 2. Ensure `custom-addons` is on the addons path

**Config file** (`odoo.conf` in project root — create if missing):

```ini
[options]
admin_passwd = admin
db_host = False
db_port = False
db_user = YOUR_PG_USER
db_password = False
addons_path = odoo/addons,odoo/odoo/addons,custom-addons
http_port = 8069
```

Paths are relative to where you start `odoo-bin`, or use absolute paths.

**Or CLI only:**

```bash
./odoo/odoo-bin \
  -d cems_dev \
  --addons-path=odoo/addons,odoo/odoo/addons,custom-addons \
  --dev=all
```

> Put **`custom-addons`** (parent folder) in `addons_path`, not `construction_progress` itself.

### 3. Start Odoo

```bash
cd /path/to/pmg-odoo
source venv/bin/activate
./odoo/odoo-bin -c odoo.conf
# or:
./odoo/odoo-bin -d cems_dev --addons-path=odoo/addons,odoo/odoo/addons,custom-addons
```

Open [http://localhost:8069](http://localhost:8069).

### 4. Install the module

1. Log in as **Administrator**.
2. Enable **Developer Mode** (Settings → Activate Developer Mode).
3. **Apps → Update Apps List**.
4. Remove the “Apps” filter; search **CEMS Construction Progress** (or `construction_progress`).
5. Click **Install**.

Odoo will pull in `project` and `hr_timesheet` if needed.

**CLI install / first-time DB:**

```bash
./odoo/odoo-bin -d cems_dev \
  --addons-path=odoo/addons,odoo/odoo/addons,custom-addons \
  -i construction_progress \
  --stop-after-init
```

### 5. Upgrade after code changes

```bash
./odoo/odoo-bin -d cems_dev \
  --addons-path=odoo/addons,odoo/odoo/addons,custom-addons \
  -u construction_progress \
  --stop-after-init
```

Then start Odoo normally again. During UI/XML work, `--dev=all` helps reload views.

---

## Currency (IDR / Rupiah)

BAC, PV, and EV use the **company currency** (`project.currency_id` → `company_id.currency_id`).

On first install, the module activates **IDR (Rp)** and sets the main company currency to IDR. After that, change it only via the UI if needed:

1. **Settings → Currencies** — open **IDR**, tick **Active** (if inactive).
2. **Settings → Companies → Your Company** — set **Currency** to **IDR**.
3. Refresh the project form — BAC / PV / EV should show **Rp**.

> Changing company currency after you already have invoices/journal entries can be risky. Prefer setting IDR early on a fresh database.

---

## How to use (end users)

### A. Assign CEMS roles

1. **Settings → Users & Companies → Users**
2. Open a user → tab **Access Rights**
3. Under category **CEMS**, pick the group, e.g.:

| Group | Typical use |
|-------|-------------|
| CEMS User | Base internal CEMS access |
| Site Engineer | Update progress on assigned projects |
| Site Manager | Site-level approvals (later phases) |
| Project Manager | Own projects; full progress |
| Project Director | Read all projects |
| HSE Officer / QC Inspector | Stable IDs; full rights in later modules |
| Procurement | Logistics later |

### B. Configure a project (Manager / Admin)

1. Open menu **CEMS → Projects** (or native **Project** app).
2. Open a project → notebook pages:

**CEMS / Geofence**

- Geofence Latitude / Longitude / Radius (m) — default radius `200`
- **Site Engineers** — users who may see/edit this project (isolation)

**Progress & EVM**

- **BAC** — Budget At Completion
- **PV** — Planned Value (manual in Phase 1)
- **Physical Progress Total (%)**, **EV**, **SPI** — computed from tasks
- **WBS Validated** — when checked, task weightages must sum to **100%**
- **WBS Weightage Sum** — soft indicator before validation

Set **Project Manager** (`user_id`) on the project as usual so manager record rules apply.

### C. Build WBS on tasks (Engineer / Manager)

1. **CEMS → Tasks** (or project’s task list).
2. On each billable task fill:

| Field | Meaning |
|-------|---------|
| WBS Code | e.g. `1.2.3` |
| Weightage (%) | \(W_i\) share of project scope |
| Physical Progress (%) | \(P_i\) physical % complete (0–100) |
| WBS Billable | Off = excluded from sums |

3. Keep billable weightages totaling **100%**, then tick **WBS Validated** on the project.

### D. Read progress / EVM

Formulas (server-side):

\[
P_{\text{total}} = \sum (W_i \times P_i)
\quad\text{(stored as %)}
\]

\[
EV = \frac{P_{\text{total}}}{100} \times BAC
\qquad
SPI = \frac{EV}{PV}
\]

Open the project **Progress & EVM** page after updating task progress.

### E. Isolation check (Site Engineer)

1. Assign the engineer on the project’s **Site Engineers** field.
2. Log in as that user — only assigned projects/tasks should appear.
3. Director (with Director group) can read all projects.

---

## Menu map

| Menu | Opens |
|------|--------|
| **CEMS** | Root app menu |
| **CEMS → Projects** | Project list |
| **CEMS → Tasks** | Task list |

Native **Project** menus still work; CEMS fields appear on the same forms via inherit.

---

## Troubleshooting

| Problem | What to check |
|---------|----------------|
| Module not in Apps | `addons_path` includes `custom-addons`; folder name is `construction_progress`; Update Apps List; restart Odoo |
| Install error on depends | Ensure Community addons path includes `project` / `hr_timesheet` |
| Geofence / EVM fields missing | Upgrade `-u construction_progress`; hard-refresh browser |
| Weightage ValidationError | Sum of billable `weightage_pct` ≠ 100 while **WBS Validated** is on |
| Engineer sees wrong projects | Set **Site Engineers** on project; user must have **Site Engineer** group |
| SPI always 0 | Fill **PV (Planned Value)** > 0 |
| View inherit crash on install | Confirm Odoo 19 xml ids (`project.edit_project`, `project.view_task_form2`, …) |

---

## Module structure (reference)

```text
custom-addons/construction_progress/
├── __manifest__.py
├── models/
│   ├── project_project.py      # geofence + EVM + engineers
│   └── project_task.py         # WBS + weightage + progress
├── views/
│   ├── project_views_inherit.xml
│   ├── project_task_views_inherit.xml
│   └── menu_items.xml
├── security/
│   ├── cems_groups.xml
│   ├── ir.model.access.csv
│   └── ir_rules.xml
└── AGENTS.md                   # AI scope for Phase 1
```

Full technical checklist: [08_phase1_construction_progress.md](./08_phase1_construction_progress.md).

---

## What’s next

After Phase 1 works end-to-end, follow [07_roadmap.md](./07_roadmap.md):

1. **Phase 2** — `construction_hrd` (geofence attendance portal)
2. **Phase 3** — Daily Site Report + logistics  
…
