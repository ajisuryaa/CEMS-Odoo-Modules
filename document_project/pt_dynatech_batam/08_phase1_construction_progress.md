# Phase 1 — Core Foundation: `construction_progress`

**Landasan AI** untuk mengerjakan Phase 1 CEMS (PT Dynatech Batam).  
Baca juga: [AGENTS.md](./AGENTS.md) · [07_roadmap.md](./07_roadmap.md) · [03_spesifikasi_fungsional.md](./03_spesifikasi_fungsional.md) · [05_keamanan_rbac.md](./05_keamanan_rbac.md)

| Item | Nilai |
|------|--------|
| **Addon** | `construction_progress` |
| **Path kode** | `custom-addons/construction_progress/` |
| **Odoo** | **19 Community** |
| **Depends** | `project`, `hr_timesheet` |
| **Durasi blueprint** | Minggu 1–3 |
| **Out of scope Phase 1** | Daily Site Report (DSR), logistics, HRD portal — itu Phase 2/3 |

---

## 1. Tujuan Phase 1

Membangun fondasi CEMS agar:

1. Role & security group CEMS tersedia di seluruh suite.
2. Proyek punya data **geofence** (dipakai Phase 2 attendance).
3. Task punya **WBS + weightage + EVM** (progress fisik & SPI).
4. Data proyek terisolasi antar user lewat **record rules**.

Tanpa Phase 1, modul lain (HRD, logistics, HSE, QC, dashboard) tidak punya fondasi yang aman.

---

## 2. Deliverable wajib (checklist AI)

- [ ] Scaffold modul Odoo 19 di `custom-addons/construction_progress/`
- [ ] `__manifest__.py`: `depends: ['project', 'hr_timesheet']`, `installable: True`
- [ ] Security groups CEMS (`res.groups`) di XML data
- [ ] Inherit `project.project` → field geofence
- [ ] Inherit `project.task` → WBS, weightage, physical progress, EVM fields + constraint
- [ ] Inherit `project.project` → computed `P_total`, EV, SPI (atau field related/computed)
- [ ] View inherit (xpath) form/list project & task
- [ ] `ir.model.access.csv` untuk field/model yang perlu
- [ ] `ir.rule` isolasi project/task per role
- [ ] **Tidak** implementasi `construction.daily.report` di Phase 1 (tunda Phase 3)

---

## 3. Struktur folder Phase 1

```text
custom-addons/construction_progress/
├── __init__.py
├── __manifest__.py
├── AGENTS.md                    # pointer ke landasan ini (opsional, disarankan)
├── models/
│   ├── __init__.py
│   ├── project_project.py       # geofence + agregat EVM proyek
│   └── project_task.py          # WBS, weightage, progress, EV task-level
├── views/
│   ├── project_views_inherit.xml
│   ├── project_task_views_inherit.xml
│   └── menu_items.xml           # menu ringan / settings CEMS bila perlu
├── security/
│   ├── cems_groups.xml          # res.groups
│   ├── ir.model.access.csv
│   └── ir_rules.xml
└── data/                        # opsional: default BAC category, dll.
```

**Jangan** buat `daily_site_report.py` di Phase 1 kecuali stub kosong bertanda `# Phase 3`.

---

## 4. Security groups (wajib di modul ini)

Definisikan group di `construction_progress` karena ini modul fondasi. XML category mis. `module_category_cems`.

| XML id (contoh) | Nama | Dipakai untuk |
|-----------------|------|----------------|
| `group_cems_director` | Project Director | Read-mostly + dashboard full (nanti) |
| `group_cems_manager` | Project Manager | Full progress, approve alur lain |
| `group_cems_engineer` | Site Engineer | Write progress/task proyek assigned |
| `group_cems_hse` | HSE Officer | Dibuat di sini agar ID stabil; hak HSE penuh di modul HSE |
| `group_cems_qc` | QC Inspector | Sama — ID stabil sejak Phase 1 |
| `group_cems_user` | CEMS User (opsional) | Base internal user CEMS |

Tambahan Phase 1 yang masuk akal (opsional):

| XML id | Nama |
|--------|------|
| `group_cems_site_manager` | Site Manager |
| `group_cems_procurement` | Procurement |

Semua group: `implied_ids` ke `base.group_user` kecuali portal (portal tidak di Phase 1).

---

## 5. Model: `project.project` (inherit)

File: `models/project_project.py`

### Field geofence (Phase 2 akan memakai)

| Field | Type | Keterangan |
|-------|------|------------|
| `geofence_latitude` | Float | Titik pusat ϕ |
| `geofence_longitude` | Float | Titik pusat λ |
| `geofence_radius` | Float | Meter; default mis. `200.0` |

### Field progress / EVM tingkat proyek

| Field | Type | Keterangan |
|-------|------|------------|
| `bac_amount` | Monetary | Budget At Completion (BAC) |
| `currency_id` | Many2one | Related company currency |
| `planned_value` | Monetary | PV (bisa manual Phase 1; auto dari schedule Phase berikutnya) |
| `physical_progress_total` | Float | Computed \(P_{total}\) % |
| `earned_value` | Monetary | Computed \(EV = P_{total}/100 \times BAC\) |
| `spi` | Float | Computed \(SPI = EV / PV\) (jaga division by zero) |

### Rumus agregat (server-side)

\[
P_{\text{total}} = \sum_{i=1}^{n} (W_i \times P_i)
\]

dengan \(W_i\) = `weightage_pct / 100`, \(P_i\) = `physical_progress_pct / 100` pada task anak yang dihitung (lihat aturan task di §6).

Simpan hasil sebagai persen 0–100 di `physical_progress_total`.

---

## 6. Model: `project.task` (inherit)

File: `models/project_task.py`

| Field | Type | Keterangan |
|-------|------|------------|
| `wbs_code` | Char, index | Kode WBS, mis. `1.2.3` |
| `weightage_pct` | Float | Bobot % terhadap total proyek (\(W_i\)) |
| `physical_progress_pct` | Float | \(P_i\) % selesai fisik (0–100) |
| `is_wbs_billable` | Boolean | Default True; task non-billable tidak masuk sum weightage |

### Constraint weightage per project

Pada create/write task (atau `@api.constrains`):

\[
\sum W_i = 100\%
\]

hanya untuk task dengan `is_wbs_billable=True` dan `project_id` sama (atau hanya leaf tasks — **keputusan Phase 1:** jumlahkan semua task billable di project yang punya `weightage_pct > 0`; dokumentasikan di docstring).

Jika sum ≠ 100 (toleransi 0.01): `ValidationError`.

> Catatan: saat draft awal proyek, constraint ketat 100% bisa mengganggu. **Rekomendasi Phase 1:** constraint aktif hanya jika `project.stage` / flag `wbs_locked` / atau tombol “Validate WBS”. Default yang aman: warning di computed field `wbs_weightage_sum` + constraint ketat saat `project.wbs_validated = True`.

Field proyek tambahan disarankan:

| Field | Type |
|-------|------|
| `wbs_validated` | Boolean |
| `wbs_weightage_sum` | Float computed |

### EVM di level task (opsional Phase 1)

Boleh hanya agregat di project; task cukup simpan \(W_i\) dan \(P_i\).

---

## 7. Views (xpath inherit)

- Inherit form `project.project`: page/group **CEMS / Geofence** + **Progress & EVM**.
- Inherit form `project.task`: setelah field deadline / description → `wbs_code`, `weightage_pct`, `physical_progress_pct`.
- List task: optional column `wbs_code`, `weightage_pct`, `physical_progress_pct`.

Gunakan `inherit_id` ke view project Odoo 19 (cek xml id aktual di `project` addon versi 19 — jangan asumsikan id Odoo 16).

---

## 8. Record rules (isolasi)

File: `security/ir_rules.xml`

### Project Manager / Director

- Manager: full pada project di mana `user_id = user.id` **atau** user adalah anggota proyek (sesuaikan field Odoo 19: `user_id`, `favorite_user_ids`, atau custom `cems_member_ids`).
- **Rekomendasi Phase 1:** tambah `cems_engineer_ids = Many2many('res.users')` di `project.project` untuk assignment Site Engineer (lebih jelas dari follower).

### Site Engineer

Domain contoh:

```python
[('cems_engineer_ids', 'in', [user.id])]
```

pada `project.project` dan pada `project.task`:

```python
[('project_id.cems_engineer_ids', 'in', [user.id])]
```

### Director

Read semua project (rule terpisah, perm read).

### Global / Manager

Full CRUD pada project yang `user_id = user.id`.

Jangan pakai `sudo()` untuk bypass isolasi di business logic Phase 1.

---

## 9. Access rights

`ir.model.access.csv`:

- Model yang di-inherit (`project.project`, `project.task`) biasanya sudah punya access dari `project`; cukup pastikan group CEMS punya hak yang sesuai lewat rule + group imply `project.group_project_user` / `project.group_project_manager` bila perlu.
- Jika menambah model baru di Phase 1 (seharusnya tidak): wajib CSV baru.

---

## 10. Manifest (kerangka)

```python
{
    'name': 'CEMS Construction Progress',
    'version': '19.0.1.0.0',
    'category': 'Construction',
    'summary': 'WBS, geofence, EVM foundation for CEMS',
    'depends': ['project', 'hr_timesheet'],
    'data': [
        'security/cems_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'views/project_views_inherit.xml',
        'views/project_task_views_inherit.xml',
        'views/menu_items.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

---

## 11. Aturan coding untuk AI (Phase 1)

1. Hanya `_inherit` — **tidak** ubah core `odoo/addons/project`.
2. Semua hitungan EVM/weightage di **Python server** (`@api.depends`), bukan hanya JS.
3. Target API Odoo **19** (cek perubahan view xml id / field project jika berbeda dari 17).
4. Bahasa UI field: English technical labels OK; string user boleh EN atau ID konsisten.
5. Jangan implement DSR, portal, atau stock di Phase 1.
6. Setelah coding: upgrade modul `-u construction_progress`.

---

## 12. Kriteria selesai (Definition of Done)

| Kriteria | Cara verifikasi |
|----------|-----------------|
| Modul install bersih | Apps → install tanpa traceback |
| Groups muncul | Settings → Users → Groups `CEMS / ...` |
| Geofence tersimpan | Edit project → isi lat/long/radius → save |
| WBS + weightage | Edit task → field muncul; sum terhitung di project |
| EVM | Isi BAC, PV, progress task → EV & SPI terisi |
| Isolasi engineer | Login engineer: hanya project di `cems_engineer_ids` |
| Core utuh | Tidak ada diff di folder core Odoo |

---

## 13. Setelah Phase 1

Lanjut [07_roadmap.md](./07_roadmap.md) **Phase 2** (`construction_hrd`) memakai field geofence di `project.project`.  
**Phase 3** menambah `construction.daily.report` yang meng-update `physical_progress_pct`.

---

## 14. Referensi silang

| Topik | Dokumen |
|-------|---------|
| Rumus \(P_{total}\), EV, SPI | [03_spesifikasi_fungsional.md](./03_spesifikasi_fungsional.md) §3.1 |
| Matriks role | [05_keamanan_rbac.md](./05_keamanan_rbac.md) |
| Inheritance xpath | [06_metodologi_dev.md](./06_metodologi_dev.md) |
| Matriks depends | [02_matriks_modul.md](./02_matriks_modul.md) |
