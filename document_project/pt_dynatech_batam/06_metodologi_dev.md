# 06 — Metodologi Development Odoo

## Aturan mutlak

**Jangan pernah** copy, modify, atau delete file standar Odoo core.

## Paradigma inheritance

Semua kustomisasi:

- Python: `_inherit`
- XML view: `inherit_id` + `<xpath>`

### Contoh Python — tambah WBS ke task

```python
from odoo import models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    wbs_code = fields.Char(string='WBS Code', index=True)
    weightage_pct = fields.Float(string='Weightage (%)')
```

### Contoh XML — inject field ke form

```xml
<record id="view_task_form_cems" model="ir.ui.view">
    <field name="name">project.task.form.cems</field>
    <field name="model">project.task</field>
    <field name="inherit_id" ref="project.view_task_form2"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='date_deadline']" position="after">
            <field name="wbs_code"/>
            <field name="weightage_pct"/>
        </xpath>
    </field>
</record>
```

## Checklist sebelum commit / PR

- [ ] Tidak ada patch ke `odoo/addons/*` core
- [ ] `depends` di manifest lengkap
- [ ] Access rights + record rules untuk model baru
- [ ] Constraint bisnis (weightage 100%, NCR lock progress, geofence) di server-side
- [ ] Nama teknis model `construction.*` konsisten
- [ ] Upgrade path: perubahan field/model aman untuk `-u module`
