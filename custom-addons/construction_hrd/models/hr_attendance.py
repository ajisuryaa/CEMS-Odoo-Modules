# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..utils import haversine_distance_m

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    """Extend attendance with selfie + geofence audit (CEMS Phase 2)."""

    _inherit = 'hr.attendance'

    cems_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Site Project',
        index=True,
        help='Project used for geofence validation at check-in.',
    )
    cems_selfie = fields.Binary(
        string='Selfie',
        attachment=True,
        help='Check-in selfie captured from the portal.',
    )
    cems_selfie_filename = fields.Char(string='Selfie Filename')
    cems_distance_m = fields.Float(
        string='Distance from Geofence (m)',
        digits=(10, 2),
        readonly=True,
        help='Haversine distance from project geofence center at check-in.',
    )
    cems_geofence_ok = fields.Boolean(
        string='Inside Geofence',
        readonly=True,
        default=False,
    )
    in_mode = fields.Selection(
        selection_add=[('portal', 'CEMS Portal')],
        ondelete={'portal': 'set default'},
    )

    @api.model
    def cems_validate_geofence(self, project, latitude, longitude):
        """Validate GPS against project geofence. Returns (ok, distance_m).

        Raises ValidationError if outside radius or geofence is not configured.
        """
        if not project:
            raise ValidationError(
                _('No site project assigned. Contact your supervisor.')
            )
        center_lat = project.geofence_latitude or 0.0
        center_lon = project.geofence_longitude or 0.0
        radius = project.geofence_radius or 0.0
        if not radius or (center_lat == 0.0 and center_lon == 0.0):
            raise ValidationError(
                _(
                    'Project "%(project)s" has no geofence configured. '
                    'Set latitude, longitude and radius on the project '
                    '(CEMS / Geofence tab).',
                    project=project.display_name,
                )
            )
        distance = haversine_distance_m(
            center_lat, center_lon, float(latitude), float(longitude)
        )
        if distance > radius:
            raise ValidationError(
                _(
                    'You are outside the site geofence '
                    '(%(distance).0f m away; allowed %(radius).0f m).',
                    distance=distance,
                    radius=radius,
                )
            )
        return True, distance

    @api.model
    def cems_portal_check_in(self, employee, latitude, longitude, selfie_b64=None, filename=None):
        """Create check-in for portal worker after geofence validation."""
        if not employee:
            raise UserError(_('No employee linked to this user.'))
        project = employee.cems_get_attendance_project()
        if not project:
            raise UserError(
                _(
                    'You are not on any project Site Team. '
                    'Ask your supervisor to add you under '
                    'Project → CEMS / Geofence → Site Team.'
                )
            )
        _ok, distance = self.cems_validate_geofence(project, latitude, longitude)

        open_att = self.sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)
        if open_att:
            raise UserError(
                _('You already have an open check-in. Please check out first.')
            )

        vals = {
            'employee_id': employee.id,
            'check_in': fields.Datetime.now(),
            'in_latitude': float(latitude),
            'in_longitude': float(longitude),
            'in_mode': 'portal',
            'cems_project_id': project.id,
            'cems_distance_m': distance,
            'cems_geofence_ok': True,
        }
        if selfie_b64:
            vals['cems_selfie'] = selfie_b64
            vals['cems_selfie_filename'] = filename or 'selfie.jpg'
        attendance = self.sudo().create(vals)
        _logger.info(
            'CEMS portal check-in created attendance=%s employee=%s project=%s distance_m=%.1f',
            attendance.id,
            employee.id,
            project.id,
            distance,
        )
        return attendance

    @api.model
    def cems_portal_check_out(self, employee, latitude=None, longitude=None):
        """Check out the latest open attendance for the employee."""
        if not employee:
            raise UserError(_('No employee linked to this user.'))
        open_att = self.sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], order='check_in desc', limit=1)
        if not open_att:
            raise UserError(_('No open check-in found.'))
        vals = {'check_out': fields.Datetime.now()}
        if latitude is not None and longitude is not None:
            vals['out_latitude'] = float(latitude)
            vals['out_longitude'] = float(longitude)
        open_att.sudo().write(vals)
        _logger.info(
            'CEMS portal check-out attendance=%s employee=%s',
            open_att.id,
            employee.id,
        )
        return open_att
