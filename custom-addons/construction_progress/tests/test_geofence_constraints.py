# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'cems')
class TestCemsProjectGeofenceConstraints(TransactionCase):
    """Project geofence field integrity (construction_progress)."""

    def test_latitude_out_of_range(self):
        with self.assertRaises(ValidationError):
            self.env['project.project'].create({
                'name': 'Bad Lat',
                'geofence_latitude': 95.0,
                'geofence_longitude': 104.0,
                'geofence_radius': 100.0,
            })

    def test_coordinates_require_positive_radius(self):
        with self.assertRaises(ValidationError):
            self.env['project.project'].create({
                'name': 'No Radius',
                'geofence_latitude': -1.13,
                'geofence_longitude': 104.05,
                'geofence_radius': 0.0,
            })
