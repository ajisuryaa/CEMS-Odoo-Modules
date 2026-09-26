# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    """Extend project.project with geofence + EVM aggregation (CEMS Phase 1)."""

    _inherit = 'project.project'

    # --- Site team (source of truth for assignment) ---
    cems_member_ids = fields.Many2many(
        comodel_name='res.users',
        relation='project_cems_member_rel',
        column1='project_id',
        column2='user_id',
        string='Site Team',
        help='All people assigned to this site. Task assignees, portal '
             'attendance, and /my/projects visibility use this list. '
             'Members are auto-shared (followers + collaborators). '
             'Assign here — not on the employee form.',
    )
    # --- Engineers subset (record-rule isolation for Site Engineer role) ---
    cems_engineer_ids = fields.Many2many(
        comodel_name='res.users',
        relation='project_cems_engineer_rel',
        column1='project_id',
        column2='user_id',
        string='Site Engineers',
        domain="[('share', '=', False)]",
        help='Internal Site Engineers for backend isolation (ir.rule). '
             'They are also added to Site Team automatically.',
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

    def _cems_sync_engineers_into_members(self):
        """Ensure every Site Engineer is also on the Site Team."""
        for project in self:
            missing = project.cems_engineer_ids - project.cems_member_ids
            if missing:
                project.cems_member_ids = [(4, uid) for uid in missing.ids]

    def _cems_sync_site_team_portal_access(self):
        """Auto-share Site Team on portal (/my/projects).

        Odoo portal only lists projects when:
        - privacy_visibility is ``invited_users`` or ``portal``, and
        - the user's partner follows the project (message_partner_ids).

        Collaborators unlock project-sharing task views for portal users.
        """
        for project in self.sudo():
            members = project.cems_member_ids
            if not members:
                continue
            partners = members.mapped('partner_id')
            if members and project.privacy_visibility not in (
                'invited_users',
                'portal',
            ):
                # Invited-only: Site Team are the invitees (not all portal users)
                project.write({'privacy_visibility': 'invited_users'})
            if partners:
                project.message_subscribe(partner_ids=partners.ids)
            # Portal / shared partners → project.collaborator
            share_partners = partners.filtered('partner_share') | members.filtered(
                'share'
            ).mapped('partner_id')
            if share_partners:
                project._add_collaborators(share_partners, limited_access=False)

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        projects._cems_sync_engineers_into_members()
        projects._cems_sync_site_team_portal_access()
        return projects

    def write(self, vals):
        res = super().write(vals)
        if 'cems_engineer_ids' in vals:
            self._cems_sync_engineers_into_members()
        if 'cems_member_ids' in vals or 'cems_engineer_ids' in vals:
            self._cems_sync_site_team_portal_access()
        return res

    @api.constrains('geofence_latitude', 'geofence_longitude', 'geofence_radius')
    def _check_cems_geofence(self):
        """Keep geofence data coherent when any coordinate/radius is set."""
        for project in self:
            has_center = bool(project.geofence_latitude or project.geofence_longitude)
            if project.geofence_radius is not None and project.geofence_radius < 0:
                raise ValidationError(
                    _('Geofence radius for project "%(project)s" cannot be negative.',
                      project=project.display_name)
                )
            if has_center and (not project.geofence_radius or project.geofence_radius <= 0):
                raise ValidationError(
                    _(
                        'Project "%(project)s" has geofence coordinates but no '
                        'positive radius. Set Geofence Radius (m).',
                        project=project.display_name,
                    )
                )
            if project.geofence_latitude and not (-90.0 <= project.geofence_latitude <= 90.0):
                raise ValidationError(_('Geofence latitude must be between -90 and 90.'))
            if project.geofence_longitude and not (-180.0 <= project.geofence_longitude <= 180.0):
                raise ValidationError(_('Geofence longitude must be between -180 and 180.'))

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
            p_total = sum(
                (t.weightage_pct / 100.0) * t.physical_progress_pct
                for t in billable
            )
            project.physical_progress_total = p_total
            bac = project.bac_amount or 0.0
            project.earned_value = (p_total / 100.0) * bac
            pv = project.planned_value or 0.0
            project.spi = (project.earned_value / pv) if pv else 0.0
