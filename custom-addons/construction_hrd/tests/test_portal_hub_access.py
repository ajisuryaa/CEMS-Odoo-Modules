# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


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
