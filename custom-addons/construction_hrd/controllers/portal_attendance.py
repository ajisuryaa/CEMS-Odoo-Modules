# -*- coding: utf-8 -*-
import base64
import logging

from odoo import _, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class CemsPortalAttendanceController(http.Controller):
    """Portal geofenced selfie attendance (CEMS Phase 2)."""

    def _get_portal_employee(self):
        """Return the hr.employee linked to the current portal/internal user."""
        user = request.env.user
        if user._is_public():
            return request.env['hr.employee']
        return request.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)],
            limit=1,
        )

    def _ensure_own_employee(self, employee):
        """Raise AccessError unless employee belongs to the current user."""
        if not employee or employee.user_id != request.env.user:
            raise AccessError(_('Access denied.'))
        return employee

    def _parse_required_gps(self, post):
        """Parse required latitude/longitude. Return (lat, lon) or None if invalid."""
        raw_lat = post.get('latitude')
        raw_lon = post.get('longitude')
        if raw_lat in (None, '') or raw_lon in (None, ''):
            return None
        try:
            return float(raw_lat), float(raw_lon)
        except (TypeError, ValueError):
            return None

    def _read_selfie(self, post):
        """Return (base64_bytes, filename) from multipart upload, or (None, None)."""
        selfie = post.get('selfie')
        if not selfie or not hasattr(selfie, 'read'):
            return None, None
        raw = selfie.read()
        if not raw:
            return None, None
        filename = getattr(selfie, 'filename', None) or 'selfie.jpg'
        return base64.b64encode(raw), filename

    def _attendance_redirect(self, *, error=None, success=None):
        if error:
            return request.redirect(f'/my/cems/attendance?error={error}')
        if success:
            return request.redirect(f'/my/cems/attendance?success={success}')
        return request.redirect('/my/cems/attendance')

    @http.route(
        '/my/cems/attendance',
        type='http',
        auth='user',
        website=True,
    )
    def portal_attendance_page(self, **kwargs):
        employee = self._get_portal_employee()
        open_att = request.env['hr.attendance']
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
        return request.render('construction_hrd.portal_attendance_page', values)

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
            return self._attendance_redirect(error='no_employee')
        self._ensure_own_employee(employee)

        gps = self._parse_required_gps(post)
        if gps is None:
            return self._attendance_redirect(error='invalid_gps')
        latitude, longitude = gps
        selfie_b64, filename = self._read_selfie(post)

        try:
            request.env['hr.attendance'].cems_portal_check_in(
                employee,
                latitude,
                longitude,
                selfie_b64=selfie_b64,
                filename=filename,
            )
        except ValidationError as err:
            _logger.info(
                'CEMS portal check-in geofence denied for employee=%s: %s',
                employee.id,
                err.args[0] if err.args else err,
            )
            return self._attendance_redirect(error='outside_geofence')
        except UserError as err:
            _logger.warning(
                'CEMS portal check-in failed for employee=%s: %s',
                employee.id,
                err.args[0] if err.args else err,
            )
            return self._attendance_redirect(error='check_in_failed')
        except Exception:
            _logger.exception(
                'CEMS portal check-in unexpected error for employee=%s',
                employee.id,
            )
            return self._attendance_redirect(error='check_in_failed')

        return self._attendance_redirect(success='checked_in')

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
        self._ensure_own_employee(employee)

        latitude = longitude = None
        raw_lat = post.get('latitude')
        raw_lon = post.get('longitude')
        if raw_lat not in (None, '') and raw_lon not in (None, ''):
            try:
                latitude = float(raw_lat)
                longitude = float(raw_lon)
            except (TypeError, ValueError):
                latitude = longitude = None

        try:
            request.env['hr.attendance'].cems_portal_check_out(
                employee, latitude=latitude, longitude=longitude
            )
        except (ValidationError, UserError) as err:
            _logger.warning(
                'CEMS portal check-out failed for employee=%s: %s',
                employee.id,
                err.args[0] if err.args else err,
            )
            return self._attendance_redirect(error='checkout_failed')
        except Exception:
            _logger.exception(
                'CEMS portal check-out unexpected error for employee=%s',
                employee.id,
            )
            return self._attendance_redirect(error='checkout_failed')

        return self._attendance_redirect(success='checked_out')

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
            _logger.info(
                'CEMS portal JSON check-in failed for employee=%s: %s',
                employee.id,
                err.args[0] if err.args else err,
            )
            return {'ok': False, 'error': err.args[0] if err.args else str(err)}
