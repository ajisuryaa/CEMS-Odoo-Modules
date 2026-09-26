# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ConstructionDailyLabor(models.Model):
    """Daily Labor Report (DLR) — headcount by trade / hire type."""

    _name = 'construction.daily.labor'
    _description = 'Daily Labor Report'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        index=True,
        tracking=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='project_id.company_id',
        store=True,
        readonly=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Prepared By',
        default=lambda self: self.env.user,
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name='construction.daily.labor.line',
        inverse_name='labor_id',
        string='Headcount Lines',
    )
    total_direct = fields.Integer(
        string='Total Direct Hire',
        compute='_compute_totals',
        store=True,
    )
    total_subcon = fields.Integer(
        string='Total Subcontractor',
        compute='_compute_totals',
        store=True,
    )
    total_headcount = fields.Integer(
        string='Total Headcount',
        compute='_compute_totals',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )
    notes = fields.Text(string='Notes')

    @api.depends('line_ids.headcount_direct', 'line_ids.headcount_subcon')
    def _compute_totals(self):
        for rec in self:
            rec.total_direct = sum(rec.line_ids.mapped('headcount_direct'))
            rec.total_subcon = sum(rec.line_ids.mapped('headcount_subcon'))
            rec.total_headcount = rec.total_direct + rec.total_subcon

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'construction.daily.labor'
                ) or _('New')
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft Daily Labor Reports can be submitted.'))
            if not rec.line_ids:
                raise UserError(_('Add at least one headcount line before submitting.'))
        self.write({'state': 'submitted'})

    def action_approve(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Only submitted Daily Labor Reports can be approved.'))
        self.write({'state': 'approved'})

    def action_reset_draft(self):
        for rec in self:
            if rec.state == 'approved':
                raise UserError(
                    _('Approved Daily Labor Reports cannot be reset. Create a correction instead.')
                )
        self.write({'state': 'draft'})


class ConstructionDailyLaborLine(models.Model):
    _name = 'construction.daily.labor.line'
    _description = 'Daily Labor Report Line'
    _order = 'trade, id'

    labor_id = fields.Many2one(
        comodel_name='construction.daily.labor',
        string='Daily Labor',
        required=True,
        ondelete='cascade',
        index=True,
    )
    trade = fields.Selection(
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
        required=True,
    )
    headcount_direct = fields.Integer(string='Direct Hire', default=0)
    headcount_subcon = fields.Integer(string='Subcontractor', default=0)
    headcount_total = fields.Integer(
        string='Total',
        compute='_compute_headcount_total',
        store=True,
    )

    @api.depends('headcount_direct', 'headcount_subcon')
    def _compute_headcount_total(self):
        for line in self:
            line.headcount_total = line.headcount_direct + line.headcount_subcon

    @api.constrains('headcount_direct', 'headcount_subcon')
    def _check_headcount_non_negative(self):
        for line in self:
            if line.headcount_direct < 0 or line.headcount_subcon < 0:
                raise ValidationError(_('Headcount values cannot be negative.'))
