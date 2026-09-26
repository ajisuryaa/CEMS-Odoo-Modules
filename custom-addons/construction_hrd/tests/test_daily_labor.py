# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'cems')
class TestCemsDailyLabor(TransactionCase):
    """DLR workflow validations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({
            'name': 'CEMS DLR Test Project',
        })

    def test_submit_requires_lines(self):
        labor = self.env['construction.daily.labor'].create({
            'project_id': self.project.id,
        })
        with self.assertRaises(UserError):
            labor.action_submit()

    def test_negative_headcount_raises(self):
        labor = self.env['construction.daily.labor'].create({
            'project_id': self.project.id,
        })
        with self.assertRaises(ValidationError):
            self.env['construction.daily.labor.line'].create({
                'labor_id': labor.id,
                'trade': 'helper',
                'headcount_direct': -1,
            })

    def test_submit_and_approve_happy_path(self):
        labor = self.env['construction.daily.labor'].create({
            'project_id': self.project.id,
            'line_ids': [(0, 0, {
                'trade': 'carpenter',
                'headcount_direct': 3,
                'headcount_subcon': 1,
            })],
        })
        labor.action_submit()
        self.assertEqual(labor.state, 'submitted')
        self.assertEqual(labor.total_headcount, 4)
        labor.action_approve()
        self.assertEqual(labor.state, 'approved')
