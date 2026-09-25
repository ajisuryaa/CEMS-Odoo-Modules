# CEMS — Construction & Engineering Management Suite

Monorepo for **PT Dynatech Batam** custom Odoo addons (CEMS) and project documentation.

| | |
|---|---|
| **Product** | Odoo Construction & Engineering Management Suite (**CEMS**) |
| **Client** | PT Dynatech Batam |
| **Target** | **Odoo 19 Community** |
| **License** | LGPL-3 (addons) |

---

## Repository layout

```text
cems_odoo/                          ← this Git repository root
├── README.md
├── RUNNING.md                      ← how to run (venv + Docker)
├── .gitignore
├── LICENSE
├── odoo.conf.example
├── docker-compose.yml
├── docker/odoo.conf
├── custom-addons/                  ← put this path in Odoo addons_path
│   ├── construction_progress/      ← Phase 1 — WBS, geofence, EVM, CEMS groups
│   └── construction_hrd/           ← Phase 2 — portal attendance, DLR, gate pass
└── document_project/
    └── pt_dynatech_batam/          ← blueprint, AGENTS, phase guides
```

**Not in this repo:** Odoo core source, Python `venv`, PostgreSQL data, real `odoo.conf` secrets.

---

## Modules (install order)

```text
construction_progress
  → construction_hrd
  → (later) construction_logistics
  → construction_engineering / construction_hse / construction_qc
  → construction_dashboard
```

| Addon | Phase | Summary |
|-------|-------|---------|
| [`construction_progress`](./custom-addons/construction_progress/) | 1 | CEMS groups, project geofence, task WBS/EVM |
| [`construction_hrd`](./custom-addons/construction_hrd/) | 2 | Employee↔project, geofenced portal attendance, DLR, gate pass |

Docs index: [`document_project/pt_dynatech_batam/README.md`](./document_project/pt_dynatech_batam/README.md)

---

## How to run

Full guide (venv **and** Docker): **[RUNNING.md](./RUNNING.md)**

Typical sibling layout:

```text
pmg-odoo/
├── odoo/                 # git clone -b 19.0 https://github.com/odoo/odoo.git
├── venv/
└── cems_odoo/            # this repository
```

**Without Docker** (from `pmg-odoo/`):

```bash
source venv/bin/activate
./odoo/odoo-bin -d odoo \
  --addons-path=odoo/addons,odoo/odoo/addons,cems_odoo/custom-addons
```

**With Docker** (from `cems_odoo/`):

```bash
docker compose up -d
```

Then install **CEMS Construction Progress**, then **CEMS Construction HRD** (see RUNNING.md).
---

## Push this repo to GitHub (first time)

```bash
cd cems_odoo

git init
git add .
git status          # confirm: no __pycache__, .DS_Store, odoo.conf secrets

git commit -m "Initial CEMS monorepo: progress, hrd, and project docs"

git branch -M main
git remote add origin git@github.com:YOUR_USER/cems-odoo.git
# or: https://github.com/YOUR_USER/cems-odoo.git

git push -u origin main
```

Create an empty repository on GitHub first (no README/license if you already have them here). Prefer **Private** for client work.

---

## Conventions

1. Never modify Odoo core — only `_inherit` / xpath in `custom-addons/`.
2. New domain addons live under `custom-addons/construction_*`.
3. Shared CEMS security groups are defined in `construction_progress`.
4. Follow the roadmap in `document_project/pt_dynatech_batam/07_roadmap.md`.

---

## Authors

Batemtech / PT Dynatech Batam
