# -*- coding: utf-8 -*-
import base64

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class CemsPortalAttendanceController(http.Controller):
    """Portal geofenced selfie attendance (CEMS Phase 2)."""

    def _get_portal_employee(self):
        user = request.env.user
        if user._is_public():
            return False
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        return employee

    @http.route(
        '/my/cems/attendance',
        type='http',
        auth='user',
        website=True,
    )
    def portal_attendance_page(self, **kwargs):
        employee = self._get_portal_employee()
        open_att = False
        if employee:
            open_att = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
            ], limit=1)
        values = {
            'employee': employee,
            'project': employee.cems_get_attendance_project() if employee else False,
            'open_attendance': open_att,
            'page_name': 'cems_attendance',
            'error': kwargs.get('error'),
            'success': kwargs.get('success'),
        }
        return request.render(
            'construction_hrd.portal_attendance_page',
            values,
        )

    @http.route(
        '/my/cems/attendance/check_in',
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def portal_check_in(self, **post):
        employee = self._get_portal_employee()
        if not employee:
            return request.redirect(
                '/my/cems/attendance?error=no_employee'
            )
        # Ownership: portal user may only check in as themselves
        if employee.user_id != request.env.user:
            raise AccessError(request.env._('Access denied.'))

        try:
            latitude = float(post.get('latitude') or 0)
            longitude = float(post.get('longitude') or 0)
        except (TypeError, ValueError):
            return request.redirect(
                '/my/cems/attendance?error=invalid_gps'
            )

        selfie_b64 = None
        filename = None
        selfie = post.get('selfie')
        if selfie and hasattr(selfie, 'read'):
            raw = selfie.read()
            if raw:
                selfie_b64 = base64.b64encode(raw)
                filename = getattr(selfie, 'filename', None) or 'selfie.jpg'

        try:
            request.env['hr.attendance'].cems_portal_check_in(
                employee,
                latitude,
                longitude,
                selfie_b64=selfie_b64,
                filename=filename,
            )
        except ValidationError:
            return request.redirect('/my/cems/attendance?error=outside_geofence')
        except UserError:
            return request.redirect('/my/cems/attendance?error=check_in_failed')

        return request.redirect('/my/cems/attendance?success=checked_in')

    @http.route(
        '/my/cems/attendance/check_out',
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def portal_check_out(self, **post):
        employee = self._get_portal_employee()
        if not employee or employee.user_id != request.env.user:
            raise AccessError(request.env._('Access denied.'))

        latitude = post.get('latitude')
        longitude = post.get('longitude')
        try:
            lat = float(latitude) if latitude not in (None, '') else None
            lon = float(longitude) if longitude not in (None, '') else None
        except (TypeError, ValueError):
            lat = lon = None

        try:
            request.env['hr.attendance'].cems_portal_check_out(
                employee, latitude=lat, longitude=lon
            )
        except (ValidationError, UserError):
            return request.redirect('/my/cems/attendance?error=checkout_failed')

        return request.redirect('/my/cems/attendance?success=checked_out')

    @http.route(
        '/my/cems/attendance/json/check_in',
        type='jsonrpc',
        auth='user',
    )
    def portal_check_in_json(self, latitude, longitude, selfie_b64=None, filename=None):
        """JSON endpoint for the frontend geolocation script."""
        employee = self._get_portal_employee()
        if not employee or employee.user_id != request.env.user:
            return {'ok': False, 'error': 'access_denied'}
        try:
            att = request.env['hr.attendance'].cems_portal_check_in(
                employee,
                latitude,
                longitude,
                selfie_b64=selfie_b64,
                filename=filename,
            )
            return {
                'ok': True,
                'attendance_id': att.id,
                'distance_m': att.cems_distance_m,
            }
        except (ValidationError, UserError) as err:
            return {'ok': False, 'error': err.args[0] if err.args else str(err)}
