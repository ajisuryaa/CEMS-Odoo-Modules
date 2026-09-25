# 01 — Arsitektur CEMS

## Ringkasan

**CEMS** menghubungkan eksekusi lapangan (site) dengan ERP Odoo. Modul native Odoo menyediakan fondasi keuangan, purchasing, inventory, HR; tujuh addon custom menambah alur kerja konstruksi.

Tujuan arsitektur: **maintainable** — core Odoo tidak disentuh; logika konstruksi diinject lewat inheritance.

## Diagram lapisan

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    Executive Construction Dashboard                     │
│               (construction_dashboard - OWL Client Action)              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────┐
│                           Custom Domain Addons                          │
├───────────────┬───────────────┬───────────────┬───────────┬─────────────┤
│  Engineering  │   Progress    │   Logistics   │  Site HRD │  HSE & QC   │
│(engineering)  │  (progress)   │  (logistics)  │  (hrd)    │ (hse / qc)  │
└───────┬───────┴───────┬───────┴───────┬───────┴─────┬─────┴──────┬──────┘
        │               │               │             │            │
┌───────▼───────────────▼───────────────▼─────────────▼────────────▼──────┐
│                            Native Odoo Core                             │
│        (project, stock, purchase, fleet, hr, account, analytic)         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Prinsip desain

| Prinsip | Artinya untuk implementasi |
|---------|----------------------------|
| Inheritance only | `_inherit` + xpath; tidak fork core |
| Domain modules | Satu concern per addon |
| Core sebagai backbone | Stock/PO/HR/Project tetap sumber kebenaran transaksi |
| Dashboard di puncak | Aggregasi KPI dari semua domain via SQL view + OWL |

## Versi dokumen

- Blueprint: **1.1.0**
- Target Odoo: **19 Community**
