# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    """Link workforce to a CEMS construction project (Phase 2)."""

    _inherit = 'hr.employee'

    cems_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Site Project',
        index=True,
        help='Construction project this worker is assigned to. '
             'Geofence attendance uses this project\'s lat/long/radius '
             '(from construction_progress).',
    )
    cems_trade = fields.Selection(
        selection=[
            ('carpenter', 'Carpenter'),
            ('mason', 'Mason'),
            ('electrician', 'Electrician'),
            ('plumber', 'Plumber'),
            ('welder', 'Welder'),
            ('helper', 'Helper'),
            ('operator', 'Operator'),
            ('other', 'Other'),
        ],
        string='Trade',
        help='Primary trade for Daily Labor Report aggregation.',
    )
    cems_hire_type = fields.Selection(
        selection=[
            ('direct', 'Direct Hire'),
            ('subcontractor', 'Subcontractor'),
        ],
        string='Hire Type',
        default='direct',
    )
