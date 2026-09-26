# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.construction_hrd.utils.geo import haversine_distance_m


@tagged('post_install', '-at_install', 'cems')
class TestCemsGeofence(TransactionCase):
    """Server-side Haversine / geofence validation (SKILL: tests + integrity)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({
            'name': 'CEMS Geofence Test Site',
            'geofence_latitude': -1.1300000,
            'geofence_longitude': 104.0530000,
            'geofence_radius': 200.0,
        })

    def test_haversine_same_point_is_zero(self):
        distance = haversine_distance_m(-1.13, 104.053, -1.13, 104.053)
        self.assertAlmostEqual(distance, 0.0, places=6)

    def test_haversine_known_short_distance(self):
        # ~111 m north of the center (approx 0.001 deg latitude)
        distance = haversine_distance_m(-1.1300, 104.0530, -1.1290, 104.0530)
        self.assertGreater(distance, 100.0)
        self.assertLess(distance, 130.0)

    def test_validate_geofence_inside(self):
        ok, distance = self.env['hr.attendance'].cems_validate_geofence(
            self.project, -1.1301, 104.0530
        )
        self.assertTrue(ok)
        self.assertLess(distance, self.project.geofence_radius)

    def test_validate_geofence_outside_raises(self):
        with self.assertRaises(ValidationError):
            self.env['hr.attendance'].cems_validate_geofence(
                self.project, -1.1500, 104.0530
            )

    def test_validate_geofence_missing_project_raises(self):
        with self.assertRaises(ValidationError):
            self.env['hr.attendance'].cems_validate_geofence(
                self.env['project.project'], -1.13, 104.053
            )

    def test_project_geofence_radius_constraint(self):
        with self.assertRaises(ValidationError):
            self.project.write({
                'geofence_latitude': -1.12,
                'geofence_longitude': 104.05,
                'geofence_radius': 0.0,
            })
