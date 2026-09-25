# -*- coding: utf-8 -*-
from odoo import api, fields, models


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
        default=lambda self: self.env._('New'),
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
            if vals.get('name', self.env._('New')) == self.env._('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'construction.gate.pass'
                ) or self.env._('New')
        return super().create(vals_list)

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_mark_used(self):
        self.write({'state': 'used'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
