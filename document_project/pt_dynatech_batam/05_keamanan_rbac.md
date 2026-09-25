# 05 — Keamanan RBAC

Dua lapisan:

1. **Model Access** (`ir.model.access.csv`) — apa yang boleh dilakukan role secara global (CRUD)
2. **Record Rules** (`ir.rule`) — baris/record mana yang boleh dilihat

## 5.1 Matriks akses (ringkas)

| Role | Group internal | Progress | Logistics | HSE | QC | Dashboard |
|------|----------------|----------|-----------|-----|-----|-----------|
| Project Director | `group_cems_director` | Read | Read | Read | Read | Full |
| Project Manager | `group_cems_manager` | Full | Approve | Approve | Approve | Project |
| Site Engineer | `group_cems_engineer` | Write | Create | Read | Create | Project |
| HSE Officer | `group_cems_hse` | Read | Read | Full | Read | HSE KPIs |
| QC Inspector | `group_cems_qc` | Read | Read | Read | Full | QC KPIs |
| Worker (Portal) | `base.group_portal` | Own Task | None | Alerts | None | None |

> Blueprint menyebut ~10 internal roles; group di atas adalah inti. Tambahkan group lain (mis. Procurement, Site Manager) konsisten dengan lifecycle MR/PTW.

## 5.2 Record rules kritis

### Isolasi Site Engineer

Engineer hanya baca/tulis Task & Daily Report pada proyek yang ditugaskan.

Contoh domain (sesuaikan field assignment aktual):

```python
[('project_id.user_id', '=', user.id)]
```

Atau domain berbasis anggota proyek jika memakai `project.project` member/follower.

### Worker geofence / attendance

Worker hanya melihat attendance & profil sendiri:

```python
[('employee_id.user_id', '=', user.id)]
```

## Catatan implementasi untuk AI

- Definisikan `res.groups` di modul fondasi (`construction_progress` / base security file bersama).
- Jangan mengandalkan hanya `sudo()` di controller portal — validasi geofence + ownership tetap di server.
- Dashboard: batasi KPI per group (Director full; HSE hanya safety KPIs; QC hanya QC KPIs).
