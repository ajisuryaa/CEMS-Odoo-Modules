# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectProject(models.Model):
    """Extend project.project with geofence + EVM aggregation (CEMS Phase 1)."""

    _inherit = 'project.project'

    # --- Assignment (record-rule isolation) ---
    cems_engineer_ids = fields.Many2many(
        comodel_name='res.users',
        relation='project_cems_engineer_rel',
        column1='project_id',
        column2='user_id',
        string='Site Engineers',
        domain="[('share', '=', False)]",
        help='Users with Site Engineer role assigned to this project '
             '(used by ir.rule isolation).',
    )

    # --- Geofence (consumed by construction_hrd Phase 2) ---
    geofence_latitude = fields.Float(
        string='Geofence Latitude',
        digits=(10, 7),
        help='Center point latitude (φ) for site attendance geofence.',
    )
    geofence_longitude = fields.Float(
        string='Geofence Longitude',
        digits=(10, 7),
        help='Center point longitude (λ) for site attendance geofence.',
    )
    geofence_radius = fields.Float(
        string='Geofence Radius (m)',
        default=200.0,
        help='Allowed distance in meters from geofence center.',
    )

    # --- WBS validation ---
    wbs_validated = fields.Boolean(
        string='WBS Validated',
        default=False,
        help='When True, billable task weightages must sum to 100%.',
    )
    wbs_weightage_sum = fields.Float(
        string='WBS Weightage Sum (%)',
        compute='_compute_wbs_weightage_sum',
        store=True,
        help='Sum of weightage_pct on billable tasks (target 100).',
    )

    # --- EVM / Progress ---
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        readonly=True,
    )
    bac_amount = fields.Monetary(
        string='BAC (Budget At Completion)',
        currency_field='currency_id',
        help='Total budget for earned value calculations.',
    )
    planned_value = fields.Monetary(
        string='PV (Planned Value)',
        currency_field='currency_id',
        help='Planned value to date. Manual in Phase 1; may auto from schedule later.',
    )
    physical_progress_total = fields.Float(
        string='Physical Progress Total (%)',
        compute='_compute_evm',
        store=True,
        help='P_total = Σ (W_i × P_i) as percent 0–100.',
    )
    earned_value = fields.Monetary(
        string='EV (Earned Value)',
        compute='_compute_evm',
        store=True,
        currency_field='currency_id',
        help='EV = (P_total / 100) × BAC.',
    )
    spi = fields.Float(
        string='SPI',
        compute='_compute_evm',
        store=True,
        help='Schedule Performance Index = EV / PV (0 if PV is 0).',
    )

    @api.depends(
        'task_ids.weightage_pct',
        'task_ids.physical_progress_pct',
        'task_ids.is_wbs_billable',
    )
    def _compute_wbs_weightage_sum(self):
        for project in self:
            billable = project.task_ids.filtered(
                lambda t: t.is_wbs_billable and t.weightage_pct > 0
            )
            project.wbs_weightage_sum = sum(billable.mapped('weightage_pct'))

    @api.depends(
        'task_ids.weightage_pct',
        'task_ids.physical_progress_pct',
        'task_ids.is_wbs_billable',
        'bac_amount',
        'planned_value',
    )
    def _compute_evm(self):
        """Server-side EVM: P_total, EV, SPI (Phase 1 formulas)."""
        for project in self:
            billable = project.task_ids.filtered(lambda t: t.is_wbs_billable)
            # P_total (%) = Σ (W_i × P_i) where W_i and P_i are fractions of 100
            p_total = sum(
                (t.weightage_pct / 100.0) * t.physical_progress_pct
                for t in billable
            )
            project.physical_progress_total = p_total
            bac = project.bac_amount or 0.0
            project.earned_value = (p_total / 100.0) * bac
            pv = project.planned_value or 0.0
            project.spi = (project.earned_value / pv) if pv else 0.0
