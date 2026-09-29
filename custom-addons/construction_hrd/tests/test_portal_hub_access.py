# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install', 'cems')
class TestCemsPortalHubMenu(TransactionCase):
    """Menu matrix: portal workers must not see Daily Labor; engineers may."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_group = cls.env.ref('base.group_portal')
        cls.engineer_group = cls.env.ref('construction_progress.group_cems_engineer')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'CEMS Portal Hub Worker',
            'login': 'cems_hub_portal_worker@example.com',
            'group_ids': [(6, 0, [cls.portal_group.id])],
        })
        cls.engineer_user = cls.env['res.users'].create({
            'name': 'CEMS Hub Engineer',
            'login': 'cems_hub_engineer@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.engineer_group.id,
            ])],
        })

    def test_portal_menu_excludes_daily_labor(self):
        user = self.portal_user
        self.assertTrue(user._is_portal())
        can_dlr = (
            not user._is_portal()
            and user.has_group('construction_progress.group_cems_engineer')
        )
        self.assertFalse(can_dlr)

    def test_engineer_menu_includes_daily_labor(self):
        user = self.engineer_user
        self.assertFalse(user._is_portal())
        can_dlr = (
            not user._is_portal()
            and user.has_group('construction_progress.group_cems_engineer')
        )
        self.assertTrue(can_dlr)


@tagged('post_install', '-at_install', 'cems')
class TestCemsPortalRouteHardening(HttpCase):
    """Audit points 1–11: block / redirect misaligned portal routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'CEMS Route Portal',
            'login': 'cems_route_portal@example.com',
            'password': 'portalportal',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.project = cls.env['project.project'].create({
            'name': 'CEMS Route Project',
            'privacy_visibility': 'portal',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'CEMS Route Task',
            'project_id': cls.project.id,
            'user_ids': [(6, 0, [cls.portal_user.id])],
        })

    def test_project_task_path_redirects_to_my_tasks(self):
        self.authenticate('cems_route_portal@example.com', 'portalportal')
        url = f'/my/projects/{self.project.id}/task/{self.task.id}'
        resp = self.url_open(url, allow_redirects=False)
        self.assertIn(resp.status_code, (301, 302, 303, 307))
        self.assertIn(f'/my/tasks/{self.task.id}', resp.headers.get('Location', ''))

    def test_project_subtasks_redirect(self):
        self.authenticate('cems_route_portal@example.com', 'portalportal')
        url = f'/my/projects/{self.project.id}/task/{self.task.id}/subtasks'
        resp = self.url_open(url, allow_redirects=False)
        self.assertIn(resp.status_code, (301, 302, 303, 307))
        self.assertIn('/my/tasks', resp.headers.get('Location', ''))

    def test_addresses_redirect_to_account(self):
        self.authenticate('cems_route_portal@example.com', 'portalportal')
        resp = self.url_open('/my/addresses', allow_redirects=False)
        self.assertIn(resp.status_code, (301, 302, 303, 307))
        self.assertIn('/my/account', resp.headers.get('Location', ''))

    def test_attendance_get_redirects_to_hub(self):
        self.authenticate('cems_route_portal@example.com', 'portalportal')
        resp = self.url_open('/my/cems/attendance', allow_redirects=False)
        self.assertIn(resp.status_code, (301, 302, 303, 307))
        location = resp.headers.get('Location', '')
        self.assertTrue(location.endswith('/my') or '/my?' in location)

    def test_signup_redirects_home(self):
        resp = self.url_open('/web/signup', allow_redirects=False)
        self.assertIn(resp.status_code, (301, 302, 303, 307))
        from urllib.parse import urlparse
        path = urlparse(resp.headers.get('Location', '')).path or '/'
        self.assertEqual(path, '/')