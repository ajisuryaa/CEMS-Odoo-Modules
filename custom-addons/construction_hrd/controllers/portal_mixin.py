# -*- coding: utf-8 -*-
"""Shared helpers for CEMS portal hub pages (Phase 1–2)."""
from odoo.http import request


class CemsPortalMixin:
    """Employee lookup + hub stats; shell menu lives on ``ir.http`` (layout C)."""

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
        return request.env['ir.http']._cems_user_can_see_daily_labor()

    def _cems_user_is_internal(self):
        return request.env.user.has_group('base.group_user')

    def _cems_portal_menu(self, page_name='home'):
        return request.env['ir.http']._cems_portal_menu(page_name)

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
            'attendance_project': (
                employee.cems_get_attendance_project() if employee else False
            ),
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
        return request.env['ir.http']._cems_portal_shell_values(
            page_name=page_name,
            page_title=page_title,
        )

    def _cems_inject_shell_values(self, values):
        """Optional merge for controllers that already build a values dict."""
        values = dict(values or {})
        page_name = values.get('page_name') or 'home'
        title = values.get('page_title') or values.get('additional_title')
        shell = request.env['ir.http']._cems_portal_shell_values(
            page_name=page_name,
            page_title=title,
        )
        # Keep a more specific title already set by the page (e.g. task name)
        if values.get('page_title'):
            shell['page_title'] = values['page_title']
        values.update(shell)
        return values
