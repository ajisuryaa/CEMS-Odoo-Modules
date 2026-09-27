# -*- coding: utf-8 -*-
"""Shared helpers for CEMS portal hub pages (Phase 1–2)."""
from odoo import _
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
    'account': 'My Profile',
    'my_details': 'My Profile',
    'cems_attendance': 'Site Attendance',
    'cems_gate_passes': 'My Gate Passes',
    'cems_daily_labor': 'Daily Labor',
}


class CemsPortalMixin:
    """Menu, shell values, and employee lookup for `/my` hub pages."""

    def _cems_get_employee(self):
        user = request.env.user
        if user._is_public():
            return request.env['hr.employee']
        return request.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)],
            limit=1,
        )

    def _cems_user_is_portal_worker(self):
        return request.env.user._is_portal()

    def _cems_user_can_see_daily_labor(self):
        """DLR menu: internal Site Engineer+ only (not portal workers)."""
        user = request.env.user
        if user._is_portal():
            return False
        return user.has_group('construction_progress.group_cems_engineer')

    def _cems_user_is_internal(self):
        return request.env.user.has_group('base.group_user')

    def _cems_menu_id_from_page_name(self, page_name):
        return CEMS_PAGE_NAME_MAP.get(page_name or 'home', page_name or 'home')

    def _cems_portal_menu(self, page_name='home'):
        """Role-aware sidebar items (Phase 1–2 only). Easy to extend later."""
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
        if self._cems_user_can_see_daily_labor():
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

    def _cems_hub_stats(self):
        """Quick stats for dashboard cards (respects ACLs / record rules)."""
        user = request.env.user
        Project = request.env['project.project']
        Task = request.env['project.task']
        GatePass = request.env['construction.gate.pass']

        if user._is_portal():
            project_count = Project.search_count([])
        else:
            project_count = Project.search_count([
                '|',
                ('cems_member_ids', 'in', user.id),
                ('user_id', '=', user.id),
            ])
            if not project_count:
                project_count = Project.search_count([])

        task_domain = [('user_ids', 'in', user.id)]
        if 'fold' in Task.env['project.task.type']._fields:
            task_domain.append(('stage_id.fold', '=', False))
        open_task_count = Task.search_count(task_domain)

        employee = self._cems_get_employee()
        open_attendance = request.env['hr.attendance']
        if employee:
            open_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
            ], limit=1)

        if user._is_portal() and employee:
            gate_domain = [
                ('employee_id', '=', employee.id),
                ('state', 'in', ('draft', 'approved')),
            ]
        else:
            gate_domain = [('state', 'in', ('draft', 'approved'))]
        try:
            gate_count = GatePass.search_count(gate_domain)
        except Exception:
            gate_count = 0

        return {
            'project_count': project_count,
            'open_task_count': open_task_count,
            'open_attendance': open_attendance,
            'checked_in': bool(open_attendance),
            'gate_pass_count': gate_count,
            'employee': employee,
        }

    def _cems_hub_lists(self, limit=5):
        """Short lists for dashboard main panel."""
        user = request.env.user
        Project = request.env['project.project']
        Task = request.env['project.task']

        if user._is_portal():
            projects = Project.search([], limit=limit, order='name')
        else:
            projects = Project.search([
                '|',
                ('cems_member_ids', 'in', user.id),
                ('user_id', '=', user.id),
            ], limit=limit, order='name')
            if not projects:
                projects = Project.search([], limit=limit, order='name')

        task_domain = [('user_ids', 'in', user.id)]
        if 'fold' in Task.env['project.task.type']._fields:
            task_domain.append(('stage_id.fold', '=', False))
        tasks = Task.search(task_domain, limit=limit, order='priority desc, id desc')

        return {
            'hub_projects': projects,
            'hub_tasks': tasks,
        }

    def _cems_prepare_shell_values(self, page_name='home', page_title=None):
        user = request.env.user
        if not page_title:
            page_title = _(CEMS_PAGE_TITLES.get(page_name, 'Portal'))
        return {
            'page_name': page_name,
            'page_title': page_title,
            'cems_menu': self._cems_portal_menu(page_name),
            'cems_user_name': user.name,
            'cems_is_internal': self._cems_user_is_internal(),
            'cems_is_portal': self._cems_user_is_portal_worker(),
            'cems_can_daily_labor': self._cems_user_can_see_daily_labor(),
            'cems_active_menu': self._cems_menu_id_from_page_name(page_name),
        }

    def _cems_inject_shell_values(self, values):
        """Merge CEMS shell into portal layout values (after page_name is known)."""
        values = dict(values or {})
        page_name = values.get('page_name') or 'home'
        title = values.get('page_title') or values.get('additional_title')
        if not title:
            title = _(CEMS_PAGE_TITLES.get(page_name, 'Portal'))
        values.update(self._cems_prepare_shell_values(
            page_name=page_name,
            page_title=title,
        ))
        return values
