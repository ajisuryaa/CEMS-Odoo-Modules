# AGENTS — `construction_progress` (Phase 1)

Modul fondasi CEMS. Sebelum coding, baca landasan lengkap:

**[document_project/pt_dynatech_batam/08_phase1_construction_progress.md](../../document_project/pt_dynatech_batam/08_phase1_construction_progress.md)**

Juga: [AGENTS.md pusat](../../document_project/pt_dynatech_batam/AGENTS.md)

## Scope Phase 1 saja

- `res.groups` CEMS
- Inherit `project.project`: geofence + BAC/PV/EV/SPI/`P_total` + **Site Team** (`cems_member_ids`)
- Inherit `project.task`: WBS, weightage, physical progress + assignees **hanya Site Team**
- Record rules isolasi (pakai `cems_engineer_ids`; engineers auto masuk Site Team)
- Odoo **19 Community**, depends: `project`, `hr_timesheet`

## Assignment rule

- Assign orang di **Project → CEMS / Geofence → Site Team** (bukan di employee form).
- Task Assignees domain = Site Team.
- Portal attendance resolve project dari Site Team membership.
- Site Team **auto-share** ke portal: set `privacy_visibility` ke `invited_users` bila perlu, `message_subscribe` partner, dan `project.collaborator` untuk user portal — agar proyek muncul di `/my/projects`.

## Jangan kerjakan di Phase 1

- `construction.daily.report` / DSR → Phase 3
- Portal GPS / HRD → Phase 2
- Material request / stock → Phase 3 logistics

## Aturan

1. Tidak modify core Odoo.
2. Hanya `_inherit` + xpath.
3. Hitung EVM/weightage di server-side Python.
