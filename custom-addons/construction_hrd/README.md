# CEMS Construction HRD

Phase 2 site workforce module — integrates with **`construction_progress`** geofence & CEMS groups.

| | |
|---|---|
| **Technical name** | `construction_hrd` |
| **Version** | `19.0.1.2.0` |
| **Depends on** | `hr`, `hr_attendance`, `mail`, `portal`, `website`, **`construction_progress`** |
| **Compatible with** | Odoo **19.0 Community** |

Full guide:  
[document_project/pt_dynatech_batam/09_phase2_construction_hrd.md](../../document_project/pt_dynatech_batam/09_phase2_construction_hrd.md)

---

## Features

- Employee → **Site Project** (uses Progress geofence)
- Portal **/my/cems/attendance** — GPS + selfie check-in; **Haversine** server validation
- **Daily Labor Report** (trade × Direct / Subcon)
- **Gate Pass** foundation
- Menus under **CEMS → Site HRD** (shared CEMS groups)

## Install order

```text
construction_progress  →  construction_hrd
```

```bash
./odoo/odoo-bin -d cems_dev \
  --addons-path=odoo/addons,odoo/odoo/addons,custom-addons \
  -i construction_hrd --stop-after-init
```

## Quick setup

1. On a **Project**: set Geofence lat / long / radius (Progress tab).
2. On an **Employee** → **CEMS / Site**:
   - Set **Access Type** → **Portal Worker only** (or Internal Team)
   - Click **Apply Access Type** (needs Work Email)
   - Add their user to **Project → Site Team**
3. Worker opens Portal → **Site Attendance** → allow GPS → selfie → Check In.
4. Backend: **CEMS → Site HRD → Attendances / Daily Labor / Gate Passes**.
