# 10 — Plan: CEMS Portal Hub (`/my`) — Role-Based Shell (Phase 1–2 scope)

**Status:** Planning document (belum implementasi)  
**Produk:** CEMS — PT Dynatech Batam  
**Odoo:** 19 Community  
**Dokumen terkait:**  
[AGENTS.md](./AGENTS.md) · [Portal_Spesification.md](../../../portal_cems/Portal_Spesification.md) ·  
[05_keamanan_rbac.md](./05_keamanan_rbac.md) · [07_roadmap.md](./07_roadmap.md) ·  
[08_phase1_construction_progress.md](./08_phase1_construction_progress.md) ·  
[09_phase2_construction_hrd.md](./09_phase2_construction_hrd.md) · [SKILL.md](../../SKILL.md)

---

## 1. Keputusan produk (dari stakeholder)

| # | Keputusan |
|---|-----------|
| 1 | Setelah login berhasil, user masuk ke **halaman hub bergaya shell dashboard** (inspirasi layout screenshot: sidebar + area konten + kartu ringkas). |
| 2 | Halaman **hanya untuk user yang sudah login** (`auth='user'`). Konten & menu mengikuti **role access**. |
| 3 | Entry point tetap **`/my`** (bukan route baru sebagai home). Sub-halaman tetap di bawah `/my/...` bila perlu. |
| 4 | Dokumen plan ini dibuat **dulu** untuk dipelajari sebelum coding. |
| 5 | **Sidebar & fitur hub hanya Phase 1 + Phase 2 yang sudah ada.** Fitur fase berikutnya (HSE, logistics, engineering, QC, executive OWL dashboard) **tidak dikerjakan** di tahap ini. |

---

## 2. Ruang lingkup vs di luar lingkup

### 2.1 In scope (Phase 1 + 2 yang sudah dibangun)

| Domain | Addon | Fitur yang boleh muncul di hub `/my` |
|--------|-------|--------------------------------------|
| Progress | `construction_progress` | Proyek (Site Team / portal share), Task (assignee Site Team), info geofence proyek (baca) |
| HRD | `construction_hrd` | Site Attendance (GPS + selfie), Gate Pass (milik sendiri), Daily Labor (**hanya role internal CEMS yang relevan**), profil akses (Access Type / Related User) |
| Auth / Website | `construction_hrd` | Login `/` sudah ada; redirect sukses → `/my` |

### 2.2 Out of scope (jangan masuk sidebar / widget dulu)

Sesuai roadmap — **belum** ada modul/implementasi siap:

- Permit to Work, Hazard Snap, SOS workflow (`construction_hse`)
- NCR / Inspection (`construction_qc`)
- Material request / PPE (`construction_logistics`)
- Drawing / EDMS / TQ (`construction_engineering`)
- S-Curve / KPI OWL Executive Dashboard (`construction_dashboard` — Phase 5, backend `/web`)
- PIN/OTP login, Public Safety Board penuh (opsional Phase 2+ polish — bukan blocker hub)

> Catatan arsitektur: **Executive Dashboard OWL** (Phase 5) tetap di back office. Hub `/my` ini adalah **Portal Action Hub** bergaya shell modern, **bukan** pengganti `construction_dashboard`.

---

## 3. Tujuan teknis

1. Ganti/override tampilan default Odoo **`portal.portal_my_home`** (`/my`) menjadi **CEMS Hub Shell** (sidebar + main).
2. Satu layout QWeb yang **mudah di-maintain**: item menu = data kecil + `groups` / helper Python, bukan hardcode besar per role.
3. Sub-page yang sudah ada (contoh `/my/cems/attendance`) memakai **layout shell yang sama** (sticky sidebar), supaya upgrade konsisten.
4. Keamanan mengikuti [05_keamanan_rbac.md](./05_keamanan_rbac.md): UI hide ≠ cukup; ACL + `ir.rule` + ownership di server tetap berlaku.

---

## 4. Persona & akses (Phase 1–2)

### 4.1 Tipe login (sudah ada di HRD)

| Access Type | Group efektif | Masuk `/web`? | Masuk `/my` hub? |
|-------------|-----------------|---------------|------------------|
| Portal Worker only | `base.group_portal` | Tidak | Ya (utama) |
| Internal Team | `base.group_user` + `group_cems_*` | Ya | Ya (boleh, setelah login CEMS `/` → `/my`) |

### 4.2 Role yang dipakai untuk menu hub (yang sudah ada group-nya)

| Role hub | Deteksi (usulan) | Catatan |
|----------|------------------|---------|
| **Portal Worker** | `user._is_portal()` | Site Team member; absensi + tugas/proyek sendiri |
| **Site Engineer** | `group_cems_engineer` (internal) | Progress + DLR create/read (aturan record sudah ada) |
| **Site / Project Manager** | `group_cems_site_manager` / `group_cems_manager` | Lebih banyak baca/approve DLR & gate pass (sesuai rule) |
| **Director** | `group_cems_director` | Read-mostly di backend; di hub: ringkasan proyek terbatas Phase 1–2 |
| **HSE / QC / Procurement groups** | Ada di XML group | **Tidak menambah menu** sampai modulnya ada — group boleh exist, menu hub = kosong tambahan |

---

## 5. Desain UI (shell) — adaptasi screenshot

Layout inspirasi: **left sidebar + top bar + main content cards**. Tema visual tetap **CEMS** (leaf/teal dari login), bukan brand screenshot.

```text
┌──────────────┬────────────────────────────────────────────┐
│ CEMS Portal  │  Top: judul halaman | user | Logout         │
│              ├────────────────────────────────────────────┤
│ Dashboard    │  Quick stats (hanya angka Phase 1–2)       │
│ My Projects  │  ┌────────┐ ┌────────┐ ┌────────┐          │
│ My Tasks     │  │ cards  │ │ cards  │ │ cards  │          │
│ Attendance   │  └────────┘ └────────┘ └────────┘          │
│ Gate Passes* │  Main panel: ringkasan / shortcut aksi     │
│ Daily Labor* │                                            │
│ ─────────    │                                            │
│ My Profile   │                                            │
└──────────────┴────────────────────────────────────────────┘
* = terlihat hanya untuk role yang diizinkan (lihat §6)
```

Mobile: sidebar collapse (off-canvas); konten utama full width — selaras filosofi mobile-first Portal Spec.

---

## 6. Matriks menu sidebar (Phase 1–2 only)

| Menu item | Route / tindakan | Portal Worker | Engineer | Site Mgr / PM | Director |
|-----------|------------------|---------------|----------|---------------|----------|
| **Dashboard** (hub home) | `/my` | ✅ | ✅ | ✅ | ✅ |
| **My Projects** | `/my/projects` (native portal + Site Team share) | ✅ | ✅ | ✅ | ✅ |
| **My Tasks** | `/my/tasks` (native portal) | ✅* | ✅ | ✅ | ✅ |
| **Site Attendance** | `/my/cems/attendance` | ✅ | ✅ | ✅ | ✅ |
| **My Gate Passes** | `/my/cems/gate_passes` *(baru, read-only own)* | ✅ | ✅ | ✅ | ✅ |
| **Daily Labor** | `/my/cems/daily_labor` *(baru, list sesuai ir.rule)* | ❌ | ✅ | ✅ | ✅ (read) |
| **My Profile** | `/my/account` atau halaman ringkas CEMS | ✅ | ✅ | ✅ | ✅ |
| Logout | `/web/session/logout` → `/` | ✅ | ✅ | ✅ | ✅ |

\* Worker: task hanya yang di-assign / follower sesuai rule portal Odoo + Site Team.

### 6.1 Quick-stat cards di `/my` (hanya data yang ada)

Usulan maksimal 4 kartu; kosongkan/hide jika tidak relevan role:

| Card | Sumber data | Portal Worker | Internal CEMS |
|------|-------------|---------------|---------------|
| My Projects (count) | `project.project` portal visible / Site Team | ✅ | ✅ |
| My Open Tasks (count) | `project.task` | ✅ | ✅ |
| Attendance status | open `hr.attendance` hari ini | ✅ | ✅ |
| Gate passes (active) | `construction.gate.pass` own / rule | ✅ | ✅ |

**Tidak** menampilkan: Total Teams, Goals, Feedback analysis, S-Curve, dll. (bukan Phase 1–2 CEMS).

### 6.2 Area utama Dashboard

Bukan chart Phase 5. Cukup:

1. **Hero aksi Attendance** — Clock In/Out shortcut → `/my/cems/attendance` (Portal Spec §3.2, sudah ada backend).
2. **Daftar singkat** My Tasks (max N) + link “View all”.
3. **Daftar singkat** My Projects.
4. Untuk Engineer+: shortcut **Daily Labor** (buat/list) jika route Phase-2 portal disiapkan.

---

## 7. Routing & struktur modul

### 7.1 Route

| Method | Path | Auth | Keterangan |
|--------|------|------|------------|
| GET | `/my` | user | Override home → CEMS Hub shell |
| GET | `/my/cems/attendance` | user | Sudah ada — bungkus layout shell |
| GET | `/my/cems/gate_passes` | user | Baru (opsional slice) — list own |
| GET | `/my/cems/daily_labor` | user | Baru (opsional slice) — filter ir.rule |
| GET | `/my/projects`, `/my/tasks` | user | Native Odoo portal — tetap; opsional inherit layout |

Login sukses (`/cems/login`) sudah redirect ke `/my` — **pertahankan**.

### 7.2 File yang diusulkan (implementasi nanti)

Tetap di **`construction_hrd`** (Phase 2 portal owner), extend Progress hanya bila butuh data project helper:

```text
construction_hrd/
├── controllers/
│   ├── website_home.py          # (existing) login
│   ├── portal_attendance.py     # (existing)
│   └── portal_hub.py            # NEW: /my override + menu context
├── views/
│   ├── portal_templates.xml     # refactor: shell + home cards
│   └── portal_hub_templates.xml # NEW: sidebar, topbar, dashboard widgets
├── static/src/css/
│   └── cems_portal_hub.css      # NEW: shell layout (sidebar)
└── tests/
    └── test_portal_hub_access.py
```

Prinsip SKILL.md: models / controllers / views / security / tests terpisah; string `_()`; log di controller.

### 7.3 Maintainability (beda role = mudah upgrade)

1. **Satu** template shell `cems_portal_layout`.
2. Menu didefinisikan sebagai **list of dict** di Python helper, mis. `_cems_portal_menu(user)`:
   - `label`, `url`, `icon`, `group_xmlids` / callable `visible(user)`.
3. QWeb hanya loop menu + `t-if` aktif (`page_name`).
4. Widget dashboard = template kecil terpisah (`cems_hub_stat_projects`, …) — modul fase nanti **inject** via inherit xpath, tanpa rewrite shell.
5. Jangan duplikasi `res.groups`; pakai group dari `construction_progress`.

---

## 8. Keamanan

| Lapisan | Aturan |
|---------|--------|
| HTTP | Semua hub route `auth='user'`; public tetap hanya `/` login |
| Portal Worker | Attendance & gate pass: `employee_id.user_id = user` (sudah ada pola) |
| Projects/Tasks | Privacy + Site Team sync Phase 1 (jangan bypass dengan `sudo()` tanpa filter) |
| Daily Labor | Hanya non-portal + `ir.rule` engineer/manager/director yang sudah ada |
| UI | Hide menu bukan pengganti ACL |

Internal user yang buka `/my`: tetap hormati record rules; jangan expose data lintas proyek.

---

## 9. Tahapan implementasi (usulan slice)

Kerjakan berurutan; tiap slice bisa di-review terpisah.

| Slice | Deliverable | Depends |
|-------|-------------|---------|
| **A — Shell** | Layout sidebar + topbar + override `/my` kosong + logout | — |
| **B — Menu matrix** | Helper menu Phase 1–2 + highlight active | A |
| **C — Stats + shortcuts** | 3–4 kartu + link Attendance / Projects / Tasks | B |
| **D — Wrap attendance** | `/my/cems/attendance` pakai `cems_portal_layout` | A |
| **E — Gate pass list (opsional)** | `/my/cems/gate_passes` read-only | B + model existing |
| **F — Daily Labor portal list (opsional)** | `/my/cems/daily_labor` untuk engineer+ | B + ir.rule |
| **G — Tests** | Login required; portal tidak lihat DLR menu; engineer melihat | B+ |

**Tidak** masuk slice ini: chart library besar, FAB multi-aksi Phase 3+, Safety Board publik.

---

## 10. Kriteria selesai (Definition of Done)

- [ ] User belum login yang buka `/my` → redirect login Odoo/portal (perilaku standar).
- [ ] Setelah `/cems/login` sukses → `/my` menampilkan CEMS Hub shell (bukan portal home default polos).
- [ ] Sidebar Portal Worker **tanpa** Daily Labor; dengan Attendance + Projects + Tasks.
- [ ] Sidebar Engineer+ menampilkan Daily Labor (jika slice F dikerjakan) atau minimal Dashboard + Progress links.
- [ ] Tidak ada menu HSE / Material / Drawing / Executive S-Curve.
- [ ] Attendance existing tetap berfungsi (GPS + selfie + Haversine).
- [ ] Upgrade modul: `-u construction_hrd` tanpa mengubah core Odoo.
- [ ] Ada test akses dasar (slice G).

---

## 11. Risiko & keputusan terbuka

| Topik | Pertanyaan untuk stakeholder | Default bila belum dijawab |
|-------|------------------------------|----------------------------|
| Internal setelah login | Apakah Internal **wajib** ke `/my`, atau boleh langsung `/web`? | Pertahankan redirect `/my` dari CEMS login; sediakan link “Open Back Office” di topbar hanya untuk `group_user` |
| Daily Labor di portal | Perlu form create di website, atau cukup list + tombol “buka di backend”? | Slice F = **list read** dulu; create tetap `/web` |
| Gate Pass portal | Hanya list own, atau juga request baru? | **List own** saja (Phase 2 fondasi) |
| Visual CSS | Seberapa dekat ke screenshot vs CEMS leaf theme? | Shell mirip struktur screenshot; warna/typography CEMS |

---

## 12. Referensi kode existing (titik mulai)

| Item | Lokasi |
|------|--------|
| Login → `/my` | `construction_hrd/controllers/website_home.py` |
| Portal home card Attendance | `views/portal_templates.xml` → inherit `portal.portal_my_home` |
| Attendance routes | `controllers/portal_attendance.py` |
| Site Team + portal share | `construction_progress/models/project_project.py` |
| Groups | `construction_progress/security/cems_groups.xml` |
| Static prototype Action Hub | `portal_cems/dashboard.html` (referensi UX; hub baru boleh beda shell) |

---

## 13. Ringkasan satu paragraf

CEMS akan mengganti **`/my`** menjadi **Portal Hub ber-sidebar** (inspirasi layout screenshot), **wajib login**, menu mengikuti role, dan **hanya menampilkan fitur Phase 1 (Progress) + Phase 2 (HRD)** yang sudah ada. Fitur fase berikutnya tidak masuk scope. Implementasi dilakukan bertahap (shell → menu → stats → wrap attendance → opsional gate pass/DLR) di modul `construction_hrd`, dengan keamanan server-side yang sudah ditetapkan di dokumen RBAC.

---

**Versi dokumen:** 1.0.0  
**Tanggal:** 2026-09-27  
**Langkah berikutnya:** Review dokumen ini → jawab §11 bila perlu → setujui slice A sebelum coding.
