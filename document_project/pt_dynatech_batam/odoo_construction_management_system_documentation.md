# Odoo Construction & Engineering Management Suite (CEMS)

## Software Architecture & Project Blueprint

## 1. Executive Summary & Architecture Overview

The **Odoo Construction & Engineering Management Suite (CEMS)** is a specialized ERP extension engineered to bridge field execution with enterprise resource planning. Native Odoo modules supply backend financial, purchasing, inventory, and human resource framework capabilities, while seven custom addons deliver domain-specific construction workflows.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Executive Construction Dashboard                     │
│               (`construction_dashboard` - OWL Client Action)             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────┐
│                           Custom Domain Addons                           │
├───────────────┬───────────────┬───────────────┬───────────┬─────────────┤
│   Engineering │   Progress    │   Logistics   │  Site HRD │   HSE & QC  │
│  (`engineering`)│  (`progress`) │  (`logistics`)│  (`hrd`)  │(`hse`/`qc`) │
└───────┬───────┴───────┬───────┴───────┬───────┴─────┬─────┴──────┬──────┘
        │               │               │             │            │
┌───────▼───────────────▼───────────────▼─────────────▼────────────▼──────┐
│                            Native Odoo Core                             │
│        (project, stock, purchase, fleet, hr, account, analytic)         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. Module Matrix & Technical Scope

| **Functional Domain**               | **Native Odoo Core Apps**               | **Custom Addon Module**    | **Key Extended & Custom Models**                                                                                    |
| :---------------------------------- | :-------------------------------------- | :------------------------- | :------------------------------------------------------------------------------------------------------------------ |
| **1. Engineering & EDMS**           | `documents`, `product`                  | `construction_engineering` | `construction.drawing`, `construction.drawing.revision`, `construction.transmittal`, `construction.technical.query` |
| **2. Construction Progress**        | `project`, `hr_timesheet`, `analytic`   | `construction_progress`    | `project.project` (extended), `project.task` (extended), `construction.daily.report`, `construction.wbs`            |
| **3. Site Logistics**               | `stock`, `purchase`, `fleet`, `account` | `construction_logistics`   | `construction.material.request`, `fleet.vehicle` (extended), `stock.picking` (extended)                             |
| **4. Site HRD & Labor**             | `hr`, `hr_contract`, `hr_attendance`    | `construction_hrd`         | `construction.daily.labor`, `construction.subcontractor`, `construction.gate.pass`, `hr.attendance` (geofenced)     |
| **5. Health, Safety & Environment** | _N/A (Built Custom)_                    | `construction_hse`         | `construction.permit.work`, `construction.safety.incident`, `construction.jsa`, `construction.ppe.log`              |
| **6. Quality Control**              | `quality` _(Enterprise/Custom)_         | `construction_qc`          | `construction.rfi`, `construction.ncr`, `construction.punch.list`, `construction.itp`                               |
| **7. Multi-Project Dashboard**      | _N/A (Built Custom)_                    | `construction_dashboard`   | `construction.dashboard.kpi.view` (SQL View), OWL Frontend Component                                                |

## 3. Functional Specifications & Calculations

### 3.1 Project Construction Progress (`construction_progress`)

Calculates work progress across structural Work Breakdown Structure (WBS) hierarchies.

- **Calculations & Earned Value Management (EVM):**
  - **Task Weightage Assignment (**$W_i$**):** Each WBS item/task is assigned a weight relative to its scope, where total project weight satisfies:
    $$
    \sum_{i=1}^{n} W_i = 100\%
    $$
  - **Physical Progress Calculation (**$P_{\text{total}}$**):**
    $$
    P_{\text{total}} = \sum_{i=1}^{n} (W_i \times P_i)
    $$
    where $P_i$ represents the actual physical completion percentage of task $i$.
  - **Earned Value Management Metrics:**
    $$
    \text{Earned Value (EV)} = P_{\text{total}} \times \text{Budget At Completion (BAC)}
    $$
    $$
    \text{Schedule Performance Index (SPI)} = \frac{\text{Earned Value (EV)}}{\text{Planned Value (PV)}}
    $$
    $$
    \text{Cost Performance Index (CPI)} = \frac{\text{Earned Value (EV)}}{\text{Actual Cost (AC)}}
    $$

### 3.2 Site Logistics & Asset Management (`construction_logistics`)

Manages site material supply lines, temporary site storage locations, and heavy machinery utilization.

- **Material Requisition (MR) Lifecycle:** `Draft` $\rightarrow$ `Submitted` $\rightarrow$ `Site Manager Approved` $\rightarrow$ `Fulfilling (Stock Transfer / Purchase Order)` $\rightarrow$ `Delivered to Site`.
- **Site Inventory Topology:** Pre-configures project location hierarchies under `Physical Locations / Project Site / [Zone]`.

### 3.3 Site Human Resources Development (`construction_hrd`)

Tracks direct workers, daily freelance labor, subcontractor crew counts, and individual worker attendance.

- **Daily Labor Report (DLR):** Categorizes manpower inputs by trade (Carpenters, Steel Fixers, Masons, Welders, General Laborers).
- **Subcontractor Site Gate Passes:** Enforces valid medical checks, orientation records, and active safety passes prior to site entry authorization.
- **Geofenced Selfie Attendance System (Portal Interface):**
  - Individual Site Workers log into a mobile-friendly Odoo Web Portal.
  - The system forces a live selfie capture via the device's front camera and extracts HTML5 GPS coordinates.
  - **Geofence Validation Logic:** The backend calculates the distance between the worker's coordinates and the assigned project's center coordinates using the **Haversine Formula**:
    $$
    d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\phi_2 - \phi_1}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\lambda_2 - \lambda_1}{2}\right)}\right)
    $$
    _Where:_
    - $d$ = Distance in meters
    - $r$ = Radius of Earth ($6,371,000$ meters)
    - $\phi_1, \phi_2$ = Latitude of site and worker (in radians)
    - $\lambda_1, \lambda_2$ = Longitude of site and worker (in radians)
  - The clock-in is **accepted** only if $d \le \text{geofence\_radius}$ (e.g., 500m).

### 3.4 Health, Safety & Environment (`construction_hse`)

Ensures compliance with site safety standards and zero-harm mandates.

- **Permit to Work (PTW) Workflow:** State-machine control for critical risk tasks.
- **Incident & Lost Time Injury (LTI) Metrics:**
  $$
  \text{LTI Frequency Rate (LTIFR)} = \left( \frac{\text{Number of LTIs} \times 1,000,000}{\text{Total Hours Worked}} \right)
  $$

### 3.5 Quality Control (`construction_qc`)

Handles inspection standards, structural approvals, and non-compliance tracking.

- **Request for Inspection (RFI):** Formally submitted by site teams to request third-party consultant sign-offs.
- **Non-Conformance Report (NCR) Lifecycle:** `Issued` $\rightarrow$ `Rework Assigned` $\rightarrow$ `Corrective Action Applied` $\rightarrow$ `Re-Inspected` $\rightarrow$ `Signed Off & Closed`. Unclosed critical NCRs automatically block associated project milestones.

### 3.6 Engineering & Document Management System (`construction_engineering`)

Maintains technical integrity across drawings and technical query records.

- **Drawing Revision Control:** Maintains version control tracking (`Rev 0`, `Rev A`, `Approved for Construction - AFC`, `As-Built`).

### 3.7 Executive Dashboard (`construction_dashboard`)

Single-pane executive interface built using OWL (Odoo Web Library) client actions.

- Displays S-Curves, HSE Safety Tickers, QC Health Indexes, and Financial Metrics.

## 4. System File & Directory Architecture

```
custom_addons/
├── construction_engineering/
├── construction_progress/
├── construction_logistics/
├── construction_hrd/
│   ├── __manifest__.py
│   ├── controllers/ (attendance_portal.py)       <-- Portal routing for selfie/GPS upload
│   ├── models/ (daily_labor.py, gate_pass.py, hr_attendance_extend.py) <-- Geofence logic
│   ├── views/ (daily_labor_views.xml, attendance_portal_templates.xml)
│   ├── static/src/js/ (geolocation_camera.js)    <-- HTML5 integration
│   └── security/ (ir.model.access.csv)
├── construction_hse/
├── construction_qc/
└── construction_dashboard/
```

## 5. Security & Access Control Matrix

The platform enforces Role-Based Access Control (RBAC) via standard Odoo Security Groups (`res.groups`) and Record Rules (`ir.rule`).

| **Role**                 | **Progress**    | **Logistics** | **Site HRD & Labor**     | **HSE**     | **QC**      | **Engineering** | **Dashboard**  |
| :----------------------- | :-------------- | :------------ | :----------------------- | :---------- | :---------- | :-------------- | :------------- |
| **System Admin**         | CRWD            | CRWD          | CRWD                     | CRWD        | CRWD        | CRWD            | CRWD           |
| **Project Director**     | Read            | Read          | Read                     | Read        | Read        | Read            | Full Access    |
| **Project Manager**      | Full Access     | Approve       | Read                     | Approve     | Approve     | Approve         | Project View   |
| **Site Engineer**        | Write (DSR)     | Create MR     | Read                     | Read        | Create RFI  | Read            | Project View   |
| **QC Inspector**         | Read            | Read          | Read                     | Read        | Full Access | Read            | QC View        |
| **HSE Officer**          | Read            | Read          | Read                     | Full Access | Read        | Read            | HSE View       |
| **Site Logistics**       | Read            | Full Access   | Read                     | Read        | Read        | Read            | Logistics View |
| **Site HR Officer**      | Read            | Read          | Full Access              | Read        | Read        | Read            | HR View        |
| **EDMS Controller**      | Read            | Read          | Read                     | Read        | Read        | Full Access     | Eng. View      |
| **Client Rep (Portal)**  | Read (S-Curve)  | -             | -                        | Read        | Approve RFI | Approve Dwg     | Portal View    |
| **Site Worker (Portal)** | Read (Own Task) | -             | **CR (Self Attendance)** | Read Alerts | -           | -               | Portal Mobile  |

## 4. Development Methodology (Odoo Best Practices)

To ensure system stability, seamless version upgrades, and maintainability, this project strictly adheres to the Odoo Inheritance Architecture. **Under no circumstances will core Odoo modules be duplicated or directly modified.**

### 4.1. The 3-Step Customization Rule

For every module in this suite, development will follow this hierarchy:

1. **Inherit Standard Apps:** Extend core Odoo modules (`project`, `hr`, `stock`) using Python `_inherit` and XML `XPath` to add specific fields (e.g., adding `wbs_code` to `project.task`).
2. **Leverage OCA / Community Apps:** Utilize established free apps from the Odoo Community Association (OCA) or App Store as a base (e.g., Document Management, Material Requisitions), and inherit them to apply construction-specific logic.
3. **Build from Scratch:** Only create completely new data models (`_name = 'new.model'`) for workflows that do not exist in standard Odoo (e.g., HSE Permit to Work, QC Non-Conformance Reports).

---

## 5. Prioritized Development Roadmap

Because ERP systems rely on strict relational data dependencies, the modules must be developed in the following priority sequence. You cannot log a material requisition against a task that doesn't exist, nor can you build a dashboard without underlying data.

### Priority 1: The Foundation (WBS & Security)

**Module:** `construction_progress` (Phase 1)

- **Goal:** Establish the database core that all other modules will connect to.
- **Tasks:**
  - Define all 11 User Roles in XML (`res.groups`).
  - Inherit `project.project` to add Geofence parameters (Latitude, Longitude, Radius).
  - Inherit `project.task` to add WBS Codes, Weightage ($W_i$), and Physical Progress fields.

### Priority 2: The Workforce (HR & Mobile Attendance)

**Module:** `construction_hrd`

- **Goal:** Create worker profiles so they can be assigned to the projects built in Priority 1.
- **Tasks:**
  - Inherit `hr.employee` to link workers to specific construction sites.
  - Implement the Python backend logic for the Haversine distance formula (Geofencing).
  - Develop the Odoo Portal web interface for workers to submit HTML5 GPS coordinates and mobile selfies.

### Priority 3: The Blueprints (Engineering & EDMS)

**Module:** `construction_engineering`

- **Goal:** Establish approved engineering drawings required for execution and Quality Control.
- **Tasks:**
  - Install a free community Document Management System (e.g., Muk Documents or OCA DMS).
  - Inherit the document model to add Construction Statuses (For Review, AFC, As-Built).
  - Build the Document Transmittal and Technical Query (TQ) workflows.

### Priority 4: Execution & Tracking (Daily Reports)

**Module:** `construction_progress` (Phase 2)

- **Goal:** Allow site engineers to log daily work against the established tasks.
- **Tasks:**
  - Create the `construction.daily.report` (DSR) model from scratch.
  - Link DSR inputs to automatically update the Physical Progress percentage on `project.task`.

### Priority 5: The Supplies (Logistics & Equipment)

**Module:** `construction_logistics`

- **Goal:** Manage the physical materials and heavy equipment used during execution.
- **Tasks:**
  - Install standard `stock`, `purchase`, and a free OCA Material Requisition app.
  - Inherit the requisition app to enforce project-based access rules.
  - Inherit `fleet.vehicle` to track excavator/crane Hobbs meter hours and fuel logs.

### Priority 6: Compliance (HSE & Quality Control)

**Modules:** `construction_hse` & `construction_qc`

- **Goal:** Track safety and quality events linked to active tasks, employees, and drawings.
- **Tasks:**
  - Build `construction.qc.ncr` (Non-Conformance) and link to `project.task`.
  - Build `construction.hse.ptw` (Permit to Work) with multi-level approval states (Draft $\rightarrow$ Submitted $\rightarrow$ Approved).

### Priority 7: Analytics (Executive Dashboard)

**Module:** `construction_dashboard`

- **Goal:** Aggregate data from all previous modules into visual KPIs.
- **Tasks:**
  - Create PostgreSQL read-only views for fast data aggregation (SPI, CPI, S-Curve).
  - Build OWL (Odoo Web Library) frontend components to render interactive charts for Executive users.
