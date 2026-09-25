# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import email_normalize


class HrEmployee(models.Model):
    """CEMS workforce fields. Site project comes from Project → Site Team."""

    _inherit = 'hr.employee'

    cems_access_type = fields.Selection(
        selection=[
            ('internal', 'Internal Team (back office)'),
            ('portal', 'Portal Worker only'),
        ],
        string='Access Type',
        help='Internal Team: can log into Odoo back office (/web).\n'
             'Portal Worker only: website portal (/my) only — no back office.\n'
             'Click “Apply Access Type” after choosing.',
    )
    cems_access_actual = fields.Selection(
        selection=[
            ('none', 'No linked user'),
            ('portal', 'Portal only'),
            ('internal', 'Internal (back office)'),
            ('other', 'Other / public'),
        ],
        string='Current Login Access',
        compute='_compute_cems_access_actual',
        help='Actual access of the Related User (not the intended Access Type).',
    )
    cems_access_mismatch = fields.Boolean(
        string='Access Mismatch',
        compute='_compute_cems_access_actual',
    )

    cems_project_ids = fields.Many2many(
        comodel_name='project.project',
        string='Site Projects',
        compute='_compute_cems_projects',
        help='Projects where this employee\'s user is on the Site Team.',
    )
    cems_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Site Project',
        compute='_compute_cems_projects',
        help='Primary site project (first Site Team membership). '
             'Assign people on the project form, not here.',
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

    @api.depends('user_id', 'user_id.share', 'user_id.group_ids', 'user_id.active')
    def _compute_cems_access_actual(self):
        for employee in self:
            user = employee.user_id
            if not user:
                employee.cems_access_actual = 'none'
            elif user._is_internal():
                employee.cems_access_actual = 'internal'
            elif user._is_portal():
                employee.cems_access_actual = 'portal'
            else:
                employee.cems_access_actual = 'other'
            employee.cems_access_mismatch = bool(
                employee.cems_access_type
                and employee.cems_access_actual
                not in ('none', employee.cems_access_type)
            )

    @api.depends('user_id')
    def _compute_cems_projects(self):
        Project = self.env['project.project'].sudo()
        for employee in self:
            if not employee.user_id:
                employee.cems_project_ids = False
                employee.cems_project_id = False
                continue
            projects = Project.search([
                ('cems_member_ids', 'in', employee.user_id.id),
            ])
            employee.cems_project_ids = projects
            employee.cems_project_id = projects[:1] if projects else False

    def cems_get_attendance_project(self):
        """Resolve site project for portal geofence (Site Team membership)."""
        self.ensure_one()
        if self.user_id:
            projects = self.env['project.project'].sudo().search([
                ('cems_member_ids', 'in', self.user_id.id),
            ], limit=1)
            return projects
        return self.env['project.project']

    def _cems_get_access_partner(self):
        """Partner used for portal / login (work contact preferred)."""
        self.ensure_one()
        partner = self.work_contact_id or self.user_id.partner_id
        if not partner:
            raise UserError(_(
                'Employee "%(name)s" has no work contact. '
                'Set Work Email first so Odoo can create a contact.',
                name=self.name,
            ))
        return partner

    def _cems_get_access_email(self):
        self.ensure_one()
        email = email_normalize(self.work_email or self._cems_get_access_partner().email or '')
        if not email:
            raise UserError(_(
                'Employee "%(name)s" needs a valid Work Email before '
                'applying Access Type.',
                name=self.name,
            ))
        return email

    def action_cems_apply_access_type(self):
        """Apply Access Type: portal-only worker or internal back-office user."""
        if not self:
            return True
        missing = self.filtered(lambda e: not e.cems_access_type)
        if missing:
            raise UserError(_(
                'Choose Access Type first (Internal Team or Portal Worker only).'
            ))
        actions = []
        for employee in self:
            if employee.cems_access_type == 'portal':
                employee._cems_ensure_portal_user()
            elif employee.cems_access_type == 'internal':
                result = employee._cems_ensure_internal_user()
                if isinstance(result, dict):
                    actions.append(result)
        if len(self) == 1 and actions:
            return actions[0]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Access Type'),
                'message': _('Access applied for %s employee(s).', len(self)),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _cems_ensure_portal_user(self):
        """Create/convert Related User to Portal only (no back office)."""
        self.ensure_one()
        partner = self._cems_get_access_partner()
        email = self._cems_get_access_email()
        if email_normalize(partner.email or '') != email:
            partner.sudo().write({'email': email})

        group_portal = self.env.ref('base.group_portal')

        user = (self.user_id or partner.with_context(active_test=False).user_ids[:1]).sudo()

        if user and user._is_internal():
            # Downgrade Internal → Portal (strip back-office groups)
            user.write({
                'active': True,
                'login': email,
                'email': email,
                'group_ids': [(6, 0, [group_portal.id])],
            })
            self.user_id = user
            user.partner_id.signup_prepare()
            self._cems_send_portal_invite(user)
            return True

        if user and user._is_portal():
            user.write({'active': True, 'login': email, 'email': email})
            self.user_id = user
            return True

        if user:
            # Public / other → force portal
            user.write({
                'active': True,
                'login': email,
                'email': email,
                'group_ids': [(6, 0, [group_portal.id])],
            })
            self.user_id = user
            user.partner_id.signup_prepare()
            self._cems_send_portal_invite(user)
            return True

        # No user yet — use portal wizard (creates user + invite email)
        wizard = self.env['portal.wizard'].with_context(
            active_ids=partner.ids,
            default_partner_ids=partner.ids,
        ).create({
            'partner_ids': [(6, 0, partner.ids)],
        })
        line = wizard.user_ids.filtered(lambda u: u.partner_id == partner)[:1]
        if not line:
            raise UserError(_('Could not open portal access for "%s".', self.name))
        line.email = email
        if line.is_internal:
            raise UserError(_(
                '"%(name)s" is linked to an Internal User. '
                'Set Access Type to Portal Worker and Apply again to convert, '
                'or clear Related User first.',
                name=self.name,
            ))
        if not line.is_portal:
            line.action_grant_access()
        new_user = partner.with_context(active_test=False).user_ids[:1]
        if not new_user:
            raise UserError(_('Portal user was not created for "%s".', self.name))
        if not new_user._is_portal() or new_user._is_internal():
            new_user.sudo().write({
                'group_ids': [(6, 0, [group_portal.id])],
                'active': True,
            })
        self.user_id = new_user
        return True

    def _cems_send_portal_invite(self, user):
        """Send portal set-password email when converting existing user."""
        template = self.env.ref(
            'auth_signup.portal_set_password_email',
            raise_if_not_found=False,
        )
        if not template:
            return
        user.partner_id.signup_prepare()
        template.with_context(
            dbname=self.env.cr.dbname,
            lang=user.lang,
            medium='portalinvite',
        ).send_mail(user.id, force_send=False)

    def _cems_ensure_internal_user(self):
        """Ensure Related User is Internal (back office). May open Create User."""
        self.ensure_one()
        group_portal = self.env.ref('base.group_portal')
        group_user = self.env.ref('base.group_user')

        if self.user_id and self.user_id._is_internal():
            return True

        if self.user_id and self.user_id._is_portal():
            # Upgrade Portal → Internal
            self.user_id.sudo().write({
                'active': True,
                'group_ids': [(3, group_portal.id), (4, group_user.id)],
            })
            return True

        if self.user_id:
            self.user_id.sudo().write({
                'active': True,
                'group_ids': [(3, group_portal.id), (4, group_user.id)],
            })
            return True

        # No user — open standard HR Create User (Internal template)
        return self.action_create_user()
