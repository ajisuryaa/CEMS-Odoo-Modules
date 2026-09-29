# -*- coding: utf-8 -*-
import logging

from odoo import _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.project.controllers.portal import ProjectCustomerPortal
from odoo.exceptions import AccessError
from odoo.http import request, route

from .portal_mixin import CemsPortalMixin

_logger = logging.getLogger(__name__)


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


class CemsProjectPortal(CemsPortalMixin, ProjectCustomerPortal):
    """Ensure /my/projects and /my/tasks get CEMS shell context values."""

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        return self._cems_inject_shell_values(values)

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
        # Always group by project for the CEMS tree list (user can still pass groupby).
        if not groupby:
            groupby = 'project_id'
        response = super().portal_my_tasks(
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
        return response
