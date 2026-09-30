# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'cems')
class TestCemsPortalNotifications(TransactionCase):
    """Site Team / task assign populate the portal notification feed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Notify Worker',
            'login': 'cems_portal_notify@example.com',
            'email': 'cems_portal_notify@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Notify Project',
        })

    def test_site_team_creates_portal_notification(self):
        Notification = self.env['cems.portal.notification']
        before = Notification.search_count([('user_id', '=', self.portal_user.id)])
        self.project.write({
            'cems_member_ids': [(4, self.portal_user.id)],
        })
        after = Notification.search_count([
            ('user_id', '=', self.portal_user.id),
            ('notification_type', '=', 'project'),
            ('is_read', '=', False),
        ])
        self.assertGreater(after, before)
        note = Notification.search([
            ('user_id', '=', self.portal_user.id),
            ('notification_type', '=', 'project'),
        ], limit=1)
        self.assertIn('/my/projects/', note.url or '')

    def test_task_assign_creates_portal_notification(self):
        self.project.write({
            'cems_member_ids': [(4, self.portal_user.id)],
        })
        Notification = self.env['cems.portal.notification']
        before = Notification.search_count([
            ('user_id', '=', self.portal_user.id),
            ('notification_type', '=', 'task'),
        ])
        task = self.env['project.task'].create({
            'name': 'Inspect Bay 2',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.portal_user.id])],
        })
        after = Notification.search_count([
            ('user_id', '=', self.portal_user.id),
            ('notification_type', '=', 'task'),
            ('res_id', '=', task.id),
        ])
        self.assertGreater(after, before)

    def test_mark_all_read(self):
        self.project.write({
            'cems_member_ids': [(4, self.portal_user.id)],
        })
        Notification = self.env['cems.portal.notification']
        unread = Notification.search_count([
            ('user_id', '=', self.portal_user.id),
            ('is_read', '=', False),
        ])
        self.assertGreater(unread, 0)
        Notification.with_user(self.portal_user).action_mark_all_read()
        self.assertEqual(
            Notification.search_count([
                ('user_id', '=', self.portal_user.id),
                ('is_read', '=', False),
            ]),
            0,
        )
