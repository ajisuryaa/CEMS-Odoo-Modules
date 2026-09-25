# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """Extend project.task with WBS, weightage, physical progress (CEMS Phase 1).

    Weightage constraint policy (Phase 1):
    - Sum all billable tasks on the project with weightage_pct > 0.
    - Strict ValidationError only when project.wbs_validated is True
      (tolerance 0.01). Otherwise rely on project.wbs_weightage_sum
      as a soft indicator.
    """

    _inherit = 'project.task'

    wbs_code = fields.Char(
        string='WBS Code',
        index=True,
        help='Work Breakdown Structure code, e.g. 1.2.3.',
    )
    weightage_pct = fields.Float(
        string='Weightage (%)',
        default=0.0,
        help='W_i — weight of this task against total project scope.',
    )
    physical_progress_pct = fields.Float(
        string='Physical Progress (%)',
        default=0.0,
        help='P_i — physical completion percent (0–100).',
    )
    is_wbs_billable = fields.Boolean(
        string='WBS Billable',
        default=True,
        help='If False, this task is excluded from weightage / P_total sums.',
    )
    # Used by assignee domain on the form (Site Team of the project)
    cems_allowed_user_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_cems_allowed_user_ids',
        string='Allowed Assignees',
    )

    @api.depends('project_id', 'project_id.cems_member_ids')
    def _compute_cems_allowed_user_ids(self):
        for task in self:
            task.cems_allowed_user_ids = task.project_id.cems_member_ids

    @api.onchange('project_id')
    def _onchange_project_id_cems_assignees(self):
        """Drop assignees that are not on the new project's Site Team."""
        if not self.project_id:
            return
        allowed = self.project_id.cems_member_ids
        if allowed:
            self.user_ids = self.user_ids & allowed

    @api.constrains('user_ids', 'project_id')
    def _check_cems_assignees_in_site_team(self):
        for task in self:
            if not task.project_id or not task.user_ids:
                continue
            allowed = task.project_id.cems_member_ids
            if not allowed:
                # No Site Team configured yet — do not block (setup phase)
                continue
            invalid = task.user_ids - allowed
            if invalid:
                raise ValidationError(
                    self.env._(
                        'Assignees must be on the project Site Team. '
                        'Invalid: %(names)s. '
                        'Add them under Project → CEMS / Geofence → Site Team.',
                        names=', '.join(invalid.mapped('name')),
                    )
                )

    @api.constrains('weightage_pct', 'physical_progress_pct')
    def _check_pct_range(self):
        for task in self:
            if not (0.0 <= task.weightage_pct <= 100.0):
                raise ValidationError(
                    self.env._('Weightage (%) must be between 0 and 100.')
                )
            if not (0.0 <= task.physical_progress_pct <= 100.0):
                raise ValidationError(
                    self.env._('Physical Progress (%) must be between 0 and 100.')
                )

    @api.constrains('weightage_pct', 'is_wbs_billable', 'project_id')
    def _check_project_weightage_sum(self):
        """Enforce Σ W_i = 100% only when project.wbs_validated is True."""
        projects = self.mapped('project_id').filtered(lambda p: p.wbs_validated)
        for project in projects:
            billable = project.task_ids.filtered(
                lambda t: t.is_wbs_billable and t.weightage_pct > 0
            )
            total = sum(billable.mapped('weightage_pct'))
            if abs(total - 100.0) > 0.01:
                raise ValidationError(
                    self.env._(
                        'WBS weightage sum for project "%(project)s" is '
                        '%(total).2f%%. It must equal 100%% when WBS is validated.',
                        project=project.display_name,
                        total=total,
                    )
                )
