# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ConstructionGatePass(models.Model):
    """Gate pass foundation — site entry/exit authorization (CEMS Phase 2)."""

    _name = 'construction.gate.pass'
    _description = 'Gate Pass'
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
        tracking=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        index=True,
        tracking=True,
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Worker',
        required=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Visitor / Company',
        help='Optional external visitor or subcontractor company.',
    )
    pass_type = fields.Selection(
        selection=[
            ('worker', 'Worker'),
            ('visitor', 'Visitor'),
            ('material', 'Material'),
            ('vehicle', 'Vehicle'),
        ],
        string='Type',
        default='worker',
        required=True,
        tracking=True,
    )
    valid_from = fields.Datetime(string='Valid From', default=fields.Datetime.now)
    valid_to = fields.Datetime(string='Valid To')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('used', 'Used'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='project_id.company_id',
        store=True,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'construction.gate.pass'
                ) or _('New')
        return super().create(vals_list)

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_window(self):
        for rec in self:
            if rec.valid_from and rec.valid_to and rec.valid_to < rec.valid_from:
                raise ValidationError(
                    _('Valid To must be on or after Valid From.')
                )

    def action_approve(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft gate passes can be approved.'))
        self.write({'state': 'approved'})

    def action_mark_used(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('Only approved gate passes can be marked as used.'))
        self.write({'state': 'used'})

    def action_cancel(self):
        for rec in self:
            if rec.state in ('used', 'cancelled'):
                raise UserError(_('Used or cancelled gate passes cannot be cancelled again.'))
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        for rec in self:
            if rec.state not in ('cancelled', 'approved'):
                raise UserError(_('Only cancelled or approved gate passes can be reset to draft.'))
        self.write({'state': 'draft'})
