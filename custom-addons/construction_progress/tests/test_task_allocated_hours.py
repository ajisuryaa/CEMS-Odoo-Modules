# -*- coding: utf-8 -*-
from datetime import datetime
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'cems')
class TestCemsTaskAllocatedHours(TransactionCase):
    """Wall-clock allocated_hours from date_start / date_deadline."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Allocated Hours Project'})

    def test_start_and_deadline(self):
        task = self.env['project.task'].create({
            'name': 'Both dates',
            'project_id': self.project.id,
            'date_start': datetime(2026, 10, 2, 1, 0, 0),   # 08:00 UTC+7 ≈ stored UTC
            'date_deadline': datetime(2026, 10, 3, 11, 0, 0),
        })
        # 34 wall-clock hours
        self.assertAlmostEqual(task.allocated_hours, 34.0, places=4)

    def test_deadline_only_uses_now(self):
        frozen_now = fields.Datetime.to_datetime('2026-10-01 10:00:00')
        deadline = fields.Datetime.to_datetime('2026-10-01 14:30:00')
        with patch.object(fields.Datetime, 'now', return_value=frozen_now):
            task = self.env['project.task'].create({
                'name': 'Deadline only',
                'project_id': self.project.id,
                'date_deadline': deadline,
            })
            self.assertAlmostEqual(task.allocated_hours, 4.5, places=4)

    def test_deadline_before_start_is_zero(self):
        task = self.env['project.task'].create({
            'name': 'Inverted',
            'project_id': self.project.id,
            'date_start': datetime(2026, 10, 3, 12, 0, 0),
            'date_deadline': datetime(2026, 10, 2, 12, 0, 0),
        })
        self.assertEqual(task.allocated_hours, 0.0)

    def test_no_deadline_is_zero(self):
        task = self.env['project.task'].create({
            'name': 'No deadline',
            'project_id': self.project.id,
            'date_start': datetime(2026, 10, 2, 8, 0, 0),
        })
        self.assertEqual(task.allocated_hours, 0.0)

    def test_manual_write_ignored(self):
        task = self.env['project.task'].create({
            'name': 'Readonly allocated',
            'project_id': self.project.id,
            'date_start': datetime(2026, 10, 1, 0, 0, 0),
            'date_deadline': datetime(2026, 10, 1, 10, 0, 0),
        })
        self.assertAlmostEqual(task.allocated_hours, 10.0, places=4)
        task.write({'allocated_hours': 99.0})
        self.assertAlmostEqual(task.allocated_hours, 10.0, places=4)
