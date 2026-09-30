# -*- coding: utf-8 -*-
"""Portal hub shell values for QWeb (self-sufficient layout — approach C)."""
from odoo import _, models
from odoo.http import request

# Map Odoo portal ``page_name`` values → CEMS sidebar item ids
CEMS_PAGE_NAME_MAP = {
    'home': 'home',
    'project': 'projects',
    'projects': 'projects',
    'task': 'tasks',
    'tasks': 'tasks',
    'project_task': 'tasks',
    'project_subtasks': 'tasks',
    'project_recurrent_tasks': 'tasks',
    'my_details': 'account',
    'account': 'account',
    'cems_attendance': 'cems_attendance',
    'cems_gate_passes': 'cems_gate_passes',
    'cems_daily_labor': 'cems_daily_labor',
}

CEMS_PAGE_TITLES = {
    'home': 'Dashboard',
    'projects': 'My Projects',
    'project': 'My Projects',
    'tasks': 'My Tasks',
    'task': 'My Tasks',
    'project_task': 'My Tasks',
    'project_subtasks': 'My Tasks',
    'project_recurrent_tasks': 'My Tasks',
    'account': 'My Profile',
    'my_details': 'My Profile',
    'cems_attendance': 'Site Attendance',
    'cems_gate_passes': 'My Gate Passes',
    'cems_daily_labor': 'Daily Labor',
}


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def _cems_menu_id_from_page_name(self, page_name):
        return CEMS_PAGE_NAME_MAP.get(page_name or 'home', page_name or 'home')

    def _cems_user_can_see_daily_labor(self, user=None):
        user = user or request.env.user
        if user._is_portal():
            return False
        return user.has_group('construction_progress.group_cems_engineer')

    def _cems_portal_menu(self, page_name='home', user=None):
        """Role-aware sidebar items (Phase 1–2 only)."""
        user = user or request.env.user
        active_id = self._cems_menu_id_from_page_name(page_name)
        items = [
            {
                'id': 'home',
                'label': 'Dashboard',
                'url': '/my',
                'icon': 'dashboard',
            },
            {
                'id': 'projects',
                'label': 'My Projects',
                'url': '/my/projects',
                'icon': 'projects',
            },
            {
                'id': 'tasks',
                'label': 'My Tasks',
                'url': '/my/tasks',
                'icon': 'tasks',
            },
            {
                'id': 'cems_attendance',
                'label': 'Site Attendance',
                'url': '/my/cems/attendance',
                'icon': 'attendance',
            },
            {
                'id': 'cems_gate_passes',
                'label': 'My Gate Passes',
                'url': '/my/cems/gate_passes',
                'icon': 'gate',
            },
        ]
        if self._cems_user_can_see_daily_labor(user):
            items.append({
                'id': 'cems_daily_labor',
                'label': 'Daily Labor',
                'url': '/my/cems/daily_labor',
                'icon': 'labor',
            })
        items.append({
            'id': 'account',
            'label': 'My Profile',
            'url': '/my/account',
            'icon': 'profile',
        })
        for item in items:
            item['active'] = item['id'] == active_id
        return items

    def _cems_portal_shell_values(self, page_name=None, page_title=None):
        """Build shell dict for ``cems_portal_layout`` (callable from QWeb).

        Always safe to call: fills menu / user flags from the current request user
        so wrapped pages do not depend on controller inject.
        """
        user = request.env.user
        page_name = page_name or 'home'
        if not page_title:
            page_title = _(CEMS_PAGE_TITLES.get(page_name, 'Portal'))
        partner = user.partner_id
        return {
            'page_name': page_name,
            'page_title': page_title,
            'cems_menu': self._cems_portal_menu(page_name, user=user),
            'cems_user_name': user.name,
            'cems_user_email': partner.email or user.login or '',
            'cems_partner_id': partner.id,
            'cems_partner_write_date': partner.write_date,
            'cems_is_internal': user.has_group('base.group_user'),
            'cems_is_portal': user._is_portal(),
            'cems_can_daily_labor': self._cems_user_can_see_daily_labor(user),
            'cems_active_menu': self._cems_menu_id_from_page_name(page_name),
        }
