# -*- coding: utf-8 -*-
"""CEMS portal route hardening for external / portal users (flow alignment)."""
import base64
import json
import logging

from odoo import _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.project.controllers.portal import ProjectCustomerPortal
from odoo.exceptions import AccessError
from odoo.http import request, route

from .portal_mixin import CemsPortalMixin

_logger = logging.getLogger(__name__)

CEMS_PROFILE_IMAGE_MAX_BYTES = 5 * 1024 * 1024


def _cems_portal_block_redirect(fallback='/my'):
    """Redirect portal users away from disallowed native portal URLs."""
    if request.env.user and not request.env.user._is_public() and request.env.user._is_portal():
        return request.redirect(fallback)
    return None


class CemsPortalHub(CemsPortalMixin, CustomerPortal):
    """CEMS role-based Portal Hub shell on `/my` (Phase 1–2 scope)."""

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        return self._cems_inject_shell_values(values)

    def _prepare_my_account_rendering_values(self, redirect='/my', **kwargs):
        values = super()._prepare_my_account_rendering_values(redirect=redirect, **kwargs)
        return self._cems_inject_shell_values(values)

    @route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kw):
        values = self._cems_prepare_shell_values(
            page_name='home',
            page_title=_('Dashboard'),
        )
        values.update(self._cems_hub_stats())
        values.update(self._cems_hub_lists(limit=5))
        values.update({
            'error': kw.get('error'),
            'success': kw.get('success'),
        })
        return request.render('construction_hrd.cems_portal_hub_home', values)

    @route(
        ['/my/cems/gate_passes'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_gate_passes(self, **kw):
        values = self._cems_prepare_shell_values(
            page_name='cems_gate_passes',
            page_title=_('My Gate Passes'),
        )
        employee = self._cems_get_employee()
        GatePass = request.env['construction.gate.pass']
        user = request.env.user
        try:
            if user._is_portal():
                if not employee:
                    passes = GatePass.browse()
                else:
                    passes = GatePass.search(
                        [('employee_id', '=', employee.id)],
                        order='date desc, id desc',
                        limit=80,
                    )
            else:
                passes = GatePass.search([], order='date desc, id desc', limit=80)
        except AccessError:
            _logger.warning('CEMS gate pass list access denied for uid=%s', user.id)
            passes = GatePass.browse()
        values.update({
            'gate_passes': passes,
            'employee': employee,
        })
        return request.render('construction_hrd.cems_portal_gate_passes', values)

    @route(
        ['/my/cems/daily_labor'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_daily_labor(self, **kw):
        if not self._cems_user_can_see_daily_labor():
            return request.redirect('/my')
        values = self._cems_prepare_shell_values(
            page_name='cems_daily_labor',
            page_title=_('Daily Labor Reports'),
        )
        Labor = request.env['construction.daily.labor']
        try:
            reports = Labor.search([], order='date desc, id desc', limit=80)
        except AccessError:
            _logger.warning(
                'CEMS daily labor list access denied for uid=%s',
                request.env.user.id,
            )
            reports = Labor.browse()
        values.update({
            'labor_reports': reports,
        })
        return request.render('construction_hrd.cems_portal_daily_labor', values)

    # --- Point 5: addresses not in CEMS flow ---
    @route('/my/addresses', type='http', auth='user', readonly=True, website=True)
    def my_addresses(self, **query_params):
        return request.redirect('/my/account')

    @route(
        '/my/address',
        type='http',
        methods=['GET'],
        auth='user',
        website=True,
        sitemap=False,
        readonly=True,
    )
    def portal_address(
        self,
        partner_id=None,
        address_type='billing',
        use_delivery_as_billing=False,
        **query_params,
    ):
        return request.redirect('/my/account')

    # --- Point 6: security in CEMS shell ---
    @route('/my/security', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def security(self, **post):
        from odoo.addons.portal.controllers.portal import get_error

        values = self._prepare_portal_layout_values()
        values['get_error'] = get_error
        values['allow_api_keys'] = bool(
            request.env['ir.config_parameter'].sudo().get_param('portal.allow_api_keys')
        )
        values['open_deactivate_modal'] = False
        values['page_name'] = 'account'
        values['page_title'] = _('Connection & Security')
        values['settings_tab'] = 'security'
        values.setdefault('errors', {})
        values.setdefault('success', {})
        values = self._cems_inject_shell_values(values)

        if request.httprequest.method == 'POST':
            values.update(self._update_password(
                post['old'].strip(),
                post['new1'].strip(),
                post['new2'].strip(),
            ))

        return request.render('construction_hrd.cems_portal_security', values, headers={
            'X-Frame-Options': 'SAMEORIGIN',
            'Content-Security-Policy': "frame-ancestors 'self'",
        })

    # --- Point 7: CEMS settings-style profile ---
    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, **kwargs):
        values = self._prepare_my_account_rendering_values(**kwargs)
        partner = values.get('partner_sudo') or request.env.user.partner_id
        employee = self._cems_get_employee()
        address_lines = [
            line for line in (
                partner.street or False,
                partner.street2 or False,
                ', '.join(
                    p for p in (
                        partner.city or '',
                        partner.state_id.name if partner.state_id else '',
                        partner.zip or '',
                    ) if p
                ) or False,
                partner.country_id.name if partner.country_id else False,
            ) if line
        ]
        values.update({
            'page_name': 'my_details',
            'page_title': _('My Profile'),
            'settings_tab': 'profile',
            'profile_edit': str(kwargs.get('edit') or '') in ('1', 'true', 'True'),
            'employee': employee,
            'site_project': (
                employee.cems_get_attendance_project() if employee else False
            ),
            'partner_address_lines': address_lines,
            'discard_url': '/my/account',
            'callback': kwargs.get('redirect') or '/my/account',
        })
        values = self._cems_inject_shell_values(values)
        response = request.render('construction_hrd.cems_portal_profile', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def _cems_save_profile_image_from_request(self):
        """Persist uploaded avatar from multipart profile save, if present."""
        uploaded = request.httprequest.files.get('image_1920')
        if not uploaded or not getattr(uploaded, 'filename', None):
            return
        raw = uploaded.read()
        if not raw:
            return
        if len(raw) > CEMS_PROFILE_IMAGE_MAX_BYTES:
            _logger.warning(
                'CEMS profile image rejected for uid=%s: size=%s',
                request.env.user.id,
                len(raw),
            )
            return
        content_type = (uploaded.mimetype or '').lower()
        if content_type and not content_type.startswith('image/'):
            _logger.warning(
                'CEMS profile image rejected for uid=%s: mimetype=%s',
                request.env.user.id,
                content_type,
            )
            return
        partner = request.env.user.partner_id.sudo()
        partner.write({'image_1920': base64.b64encode(raw)})

    @route(
        '/my/address/submit',
        type='http',
        methods=['POST'],
        auth='user',
        website=True,
        sitemap=False,
    )
    def portal_address_submit(self, partner_id=None, **form_data):
        # Drop company/VAT updates from CEMS profile form (not shown in UI).
        form_data.pop('company_name', None)
        form_data.pop('vat', None)
        response = super().portal_address_submit(partner_id=partner_id, **form_data)
        try:
            payload = json.loads(response)
        except (TypeError, ValueError, json.JSONDecodeError):
            return response
        if payload.get('redirectUrl'):
            try:
                self._cems_save_profile_image_from_request()
            except Exception:
                _logger.exception(
                    'CEMS profile image save failed for uid=%s',
                    request.env.user.id,
                )
        return response


class CemsProjectPortal(CemsPortalMixin, ProjectCustomerPortal):
    """Projects/Tasks portal routes hardened for CEMS external users."""

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        return self._cems_inject_shell_values(values)

    @route(['/my/projects', '/my/projects/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_projects(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        return super().portal_my_projects(
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            **kw,
        )

    @route(
        ['/my/projects/<int:project_id>', '/my/projects/<int:project_id>/page/<int:page>'],
        type='http',
        auth='public',
        website=True,
    )
    def portal_my_project(
        self,
        project_id=None,
        access_token=None,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        search=None,
        search_in='content',
        groupby=None,
        task_id=None,
        **kw,
    ):
        blocked = _cems_portal_block_redirect('/my/projects')
        if blocked:
            return blocked
        return super().portal_my_project(
            project_id=project_id,
            access_token=access_token,
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            search=search,
            search_in=search_in,
            groupby=groupby,
            task_id=task_id,
            **kw,
        )

    @route(
        [
            '/my/projects/<int:project_id>/project_sharing',
            '/my/projects/<int:project_id>/project_sharing/<path:subpath>',
        ],
        type='http',
        auth='user',
        methods=['GET'],
    )
    def render_project_backend_view(self, project_id, subpath=None):
        blocked = _cems_portal_block_redirect('/my/projects')
        if blocked:
            return blocked
        return super().render_project_backend_view(project_id, subpath=subpath)

    # --- Points 1–3: no project-scoped task paths in CEMS flow ---
    @route(
        '/my/projects/<int:project_id>/task/<int:task_id>',
        type='http',
        auth='public',
        website=True,
    )
    def portal_my_project_task(self, project_id=None, task_id=None, access_token=None, **kw):
        if request.env.user._is_public():
            return request.redirect('/?redirect=/my/tasks')
        if task_id:
            return request.redirect(f'/my/tasks/{task_id}')
        return request.redirect('/my/tasks')

    @route(
        '/my/projects/<int:project_id>/task/<int:task_id>/subtasks',
        type='http',
        auth='user',
        methods=['GET'],
        website=True,
    )
    def portal_my_project_subtasks(
        self,
        project_id,
        task_id,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in='content',
        groupby=None,
        **kw,
    ):
        return request.redirect('/my/tasks')

    @route(
        '/my/projects/<int:project_id>/task/<int:task_id>/recurrent_tasks',
        type='http',
        auth='user',
        methods=['GET'],
        website=True,
    )
    def portal_my_project_recurrent_tasks(
        self,
        project_id,
        task_id,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in='content',
        groupby=None,
        **kw,
    ):
        return request.redirect('/my/tasks')

    @route(['/my/tasks', '/my/tasks/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_tasks(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in='name',
        groupby=None,
        **kw,
    ):
        if not groupby:
            groupby = 'project_id'
        return super().portal_my_tasks(
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            filterby=filterby,
            search=search,
            search_in=search_in,
            groupby=groupby,
            **kw,
        )

    # --- Point 11: task detail requires login (no public token browsing) ---
    @route(['/my/tasks/<int:task_id>'], type='http', auth='user', website=True)
    def portal_my_task(
        self,
        task_id,
        report_type=None,
        access_token=None,
        project_sharing=False,
        **kw,
    ):
        return super().portal_my_task(
            task_id,
            report_type=report_type,
            access_token=access_token,
            project_sharing=project_sharing,
            **kw,
        )

    # --- Point 4 ---
    @route(
        '/project_sharing/attachment/add_image',
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
    )
    def add_image(self, name, data, res_id, access_token=None, **kwargs):
        if request.env.user._is_portal() or request.env.user._is_public():
            return request.not_found()
        return super().add_image(name, data, res_id, access_token=access_token, **kwargs)
