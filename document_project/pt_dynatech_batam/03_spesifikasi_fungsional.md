# 03 — Spesifikasi Fungsional & Model Matematika

## 3.1 Progress proyek (`construction_progress`)

Menghitung progress fisik aktual berdasarkan hierarki WBS dan mengisi analytic/keuangan.

### Bobot task (weightage) \(W_i\)

Setiap task WBS punya bobot % terhadap total scope. Constraint validasi:

\[
\sum_{i=1}^{n} W_i = 100\%
\]

### Progress fisik total \(P_{\text{total}}\)

\[
P_{\text{total}} = \sum_{i=1}^{n} (W_i \times P_i)
\]

\(P_i\) = % selesai fisik task \(i\), diupdate lewat **Daily Site Report**.

### Earned Value Management (EVM)

\[
\text{EV} = P_{\text{total}} \times \text{BAC}
\]

\[
\text{SPI} = \frac{\text{EV}}{\text{PV}}
\]

- **EV** = Earned Value  
- **BAC** = Budget At Completion  
- **PV** = Planned Value  
- **SPI** = Schedule Performance Index  

---

## 3.2 Logistics & aset (`construction_logistics`)

Menghubungkan engineer lapangan dengan procurement.

### Lifecycle Material Requisition (MR)

`Draft → Submitted → Site Manager Approved → Procurement Review → PO/Transfer Created → Received at Site`

### Equipment tracking

Extend `fleet.vehicle`: track **Hobbs meter** (engine hours) per `project.project` / analytic account untuk depresiasi mesin per proyek.

---

## 3.3 Site HRD & attendance geofence (`construction_hrd`)

### Daily Labor Report (DLR)

Form harian: headcount per trade (Carpenters, Masons, Electricians), dipisah **Direct Hire** vs **Subcontractor**.

### Geofenced selfie attendance (Portal)

- Frontend portal: `navigator.geolocation` + `<input type="file" capture="user">`
- Backend: validasi Haversine terhadap titik pusat proyek

\[
d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\phi_2-\phi_1}{2}\right)+\cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\lambda_2-\lambda_1}{2}\right)}\right)
\]

- \(d\) = jarak (meter), \(r = 6{,}371{,}000\) m  
- \(\phi\) = latitude, \(\lambda\) = longitude  
- **Rule:** jika \(d > \text{geofence\_radius}\) → `ValidationError`

---

## 3.4 HSE (`construction_hse`)

### Permit to Work (PTW)

State machine untuk pekerjaan berisiko tinggi (Hot Work, Excavation, Confined Space). Butuh tanda tangan digital HSE Officer + Site Manager sebelum kerja dimulai.

### Metrik insiden

\[
\text{LTIFR} = \left( \frac{\text{Jumlah LTI} \times 1{,}000{,}000}{\text{Total jam kerja}} \right)
\]

---

## 3.5 Quality Control (`construction_qc`)

### Non-Conformance Report (NCR)

Dikeluarkan untuk pekerjaan cacat.

**Constraint penting:** jika `project.task` punya NCR aktif/open, sistem **mengunci** field `physical_progress` (disable di form / block di `write`) sampai NCR status **Closed**.

---

## 3.6 Engineering & EDMS (`construction_engineering`)

- **Revision trees:** Rev 0, Rev 1, Rev A (As-Built)
- **Transmittal matrix:** auto-generate PDF QWeb untuk dokumen keluar ke client/consultant
