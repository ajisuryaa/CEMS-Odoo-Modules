# -*- coding: utf-8 -*-
import base64
import logging
from collections import OrderedDict
from datetime import datetime, time, timedelta

from odoo import _, fields, http
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.osv import expression

from .portal_mixin import CemsPortalMixin

_logger = logging.getLogger(__name__)

ATTENDANCE_PAGE_SIZE = 20


class CemsPortalAttendanceController(CemsPortalMixin, http.Controller):
    """Portal geofenced selfie attendance (CEMS Phase 2)."""

    def _ensure_own_employee(self, employee):
        if not employee or employee.user_id != request.env.user:
            raise AccessError(_('Access denied.'))
        return employee

    def _parse_required_gps(self, post):
        raw_lat = post.get('latitude')
        raw_lon = post.get('longitude')
        if raw_lat in (None, '') or raw_lon in (None, ''):
            return None
        try:
            return float(raw_lat), float(raw_lon)
        except (TypeError, ValueError):
            return None

    def _read_selfie(self, post):
        selfie = post.get('selfie')
        if not selfie or not hasattr(selfie, 'read'):
            return None, None
        raw = selfie.read()
        if not raw:
            return None, None
        filename = getattr(selfie, 'filename', None) or 'selfie.jpg'
        return base64.b64encode(raw), filename

    def _attendance_redirect(self, *, error=None, success=None, next_url=None):
        base = '/my'
        candidate = next_url and str(next_url)
        if candidate and candidate.startswith('/') and '//' not in candidate:
            base = candidate
        if error:
            sep = '&' if '?' in base else '?'
            return request.redirect(f'{base}{sep}error={error}')
        if success:
            sep = '&' if '?' in base else '?'
            return request.redirect(f'{base}{sep}success={success}')
        return request.redirect(base)

    def _attendance_day_bounds(self, day):
        """Naive datetime bounds for a calendar day (portal filter helpers)."""
        return (
            datetime.combine(day, time.min),
            datetime.combine(day, time.max),
        )

    def _attendance_searchbar_sortings(self):
        return OrderedDict([
            ('date_desc', {'label': _('Check-in (Newest)'), 'order': 'check_in desc, id desc'}),
            ('date_asc', {'label': _('Check-in (Oldest)'), 'order': 'check_in asc, id asc'}),
            ('checkout_desc', {'label': _('Check-out (Newest)'), 'order': 'check_out desc, id desc'}),
            ('distance', {'label': _('Distance'), 'order': 'cems_distance_m asc, check_in desc'}),
            ('project', {'label': _('Project'), 'order': 'cems_project_id, check_in desc'}),
            ('hours', {'label': _('Worked hours'), 'order': 'worked_hours desc, check_in desc'}),
        ])

    def _attendance_searchbar_filters(self):
        today = fields.Date.context_today(request.env.user)
        today_start, today_end = self._attendance_day_bounds(today)
        week_start_date = today - timedelta(days=today.weekday())
        week_start, _week_end_unused = self._attendance_day_bounds(week_start_date)
        month_start_date = today.replace(day=1)
        month_start, _month_end_unused = self._attendance_day_bounds(month_start_date)

        return OrderedDict([
            ('all', {'label': _('All'), 'domain': []}),
            ('open', {'label': _('Open (checked in)'), 'domain': [('check_out', '=', False)]}),
            ('closed', {'label': _('Closed'), 'domain': [('check_out', '!=', False)]}),
            ('today', {
                'label': _('Today'),
                'domain': [
                    ('check_in', '>=', fields.Datetime.to_string(today_start)),
                    ('check_in', '<=', fields.Datetime.to_string(today_end)),
                ],
            }),
            ('week', {
                'label': _('This week'),
                'domain': [('check_in', '>=', fields.Datetime.to_string(week_start))],
            }),
            ('month', {
                'label': _('This month'),
                'domain': [('check_in', '>=', fields.Datetime.to_string(month_start))],
            }),
            ('geofence_ok', {
                'label': _('Inside geofence'),
                'domain': [('cems_geofence_ok', '=', True)],
            }),
            ('has_selfie', {
                'label': _('With selfie'),
                'domain': [('cems_selfie_filename', '!=', False)],
            }),
        ])

    def _attendance_searchbar_groupby(self):
        return OrderedDict([
            ('none', {'label': _('None'), 'input': 'none'}),
            ('project', {'label': _('Project'), 'input': 'project'}),
            ('status', {'label': _('Status'), 'input': 'status'}),
            ('month', {'label': _('Month'), 'input': 'month'}),
        ])

    def _attendance_searchbar_inputs(self):
        return OrderedDict([
            ('all', {'input': 'all', 'label': _('Search in All')}),
            ('project', {'input': 'project', 'label': _('Search in Project')}),
        ])

    def _attendance_search_domain(self, search_in, search):
        if not search:
            return []
        search = search.strip()
        if not search:
            return []
        if search_in == 'project':
            return [('cems_project_id.name', 'ilike', search)]
        return [
            '|',
            ('cems_project_id.name', 'ilike', search),
            ('employee_id.name', 'ilike', search),
        ]

    def _group_attendances(self, records, groupby):
        """Group attendance records for the current page."""
        if not groupby or groupby == 'none':
            return [('All', records)] if records else []

        groups = OrderedDict()
        for att in records:
            if groupby == 'project':
                key = att.cems_project_id.display_name if att.cems_project_id else _('No Project')
            elif groupby == 'status':
                key = _('Open') if not att.check_out else _('Closed')
            elif groupby == 'month':
                if att.check_in:
                    key = fields.Datetime.context_timestamp(
                        att, att.check_in
                    ).strftime('%B %Y')
                else:
                    key = _('Unknown')
            else:
                key = _('All')
            groups.setdefault(key, request.env['hr.attendance'])
            groups[key] |= att
        return list(groups.items())

    def _prepare_attendance_history_values(
        self,
        page=1,
        sortby=None,
        filterby=None,
        search=None,
        search_in='all',
        groupby=None,
        **kwargs,
    ):
        employee = self._cems_get_employee()
        Attendance = request.env['hr.attendance'].sudo()

        searchbar_sortings = self._attendance_searchbar_sortings()
        searchbar_filters = self._attendance_searchbar_filters()
        searchbar_groupby = self._attendance_searchbar_groupby()
        searchbar_inputs = self._attendance_searchbar_inputs()

        if not sortby or sortby not in searchbar_sortings:
            sortby = 'date_desc'
        if not filterby or filterby not in searchbar_filters:
            filterby = 'all'
        if not groupby or groupby not in searchbar_groupby:
            groupby = 'none'
        if not search_in or search_in not in searchbar_inputs:
            search_in = 'all'

        domain = [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]
        domain = expression.AND([
            domain,
            searchbar_filters[filterby]['domain'],
            self._attendance_search_domain(search_in, search),
        ])

        # Optional custom date range (YYYY-MM-DD)
        date_begin = kwargs.get('date_begin')
        date_end = kwargs.get('date_end')
        if date_begin:
            try:
                begin = fields.Date.to_date(date_begin)
                start, _end_unused = self._attendance_day_bounds(begin)
                domain = expression.AND([
                    domain,
                    [('check_in', '>=', fields.Datetime.to_string(start))],
                ])
            except (ValueError, TypeError):
                date_begin = None
        if date_end:
            try:
                end_day = fields.Date.to_date(date_end)
                _start_unused, end = self._attendance_day_bounds(end_day)
                domain = expression.AND([
                    domain,
                    [('check_in', '<=', fields.Datetime.to_string(end))],
                ])
            except (ValueError, TypeError):
                date_end = None

        total = Attendance.search_count(domain) if employee else 0
        pager = portal_pager(
            url='/my/cems/attendance',
            total=total,
            page=page,
            step=ATTENDANCE_PAGE_SIZE,
            url_args={
                'sortby': sortby,
                'filterby': filterby,
                'search': search,
                'search_in': search_in,
                'groupby': groupby,
                'date_begin': date_begin,
                'date_end': date_end,
            },
        )
        records = Attendance.search(
            domain,
            order=searchbar_sortings[sortby]['order'],
            limit=ATTENDANCE_PAGE_SIZE,
            offset=pager['offset'],
        ) if employee else Attendance.browse()

        open_att = Attendance.browse()
        if employee:
            open_att = Attendance.search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
            ], limit=1)

        month_filter = searchbar_filters['month']['domain']
        month_count = 0
        open_count = 0
        if employee:
            month_count = Attendance.search_count(
                expression.AND([[('employee_id', '=', employee.id)], month_filter])
            )
            open_count = Attendance.search_count([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
            ])

        values = self._cems_prepare_shell_values(
            page_name='cems_attendance',
            page_title=_('Site Attendance'),
        )
        values.update({
            'employee': employee,
            'project': employee.cems_get_attendance_project() if employee else False,
            'open_attendance': open_att,
            'checked_in': bool(open_att),
            'attendances': records,
            'grouped_attendances': self._group_attendances(records, groupby),
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'filterby': filterby,
            'groupby': groupby,
            'search': search or '',
            'search_in': search_in,
            'date_begin': date_begin or '',
            'date_end': date_end or '',
            'default_url': '/my/cems/attendance',
            'attendance_total': total,
            'attendance_month_count': month_count,
            'attendance_open_count': open_count,
            'error': kwargs.get('error'),
            'success': kwargs.get('success'),
        })
        return values

    @http.route(
        ['/my/cems/attendance', '/my/cems/attendance/page/<int:page>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_attendance_page(
        self,
        page=1,
        sortby=None,
        filterby=None,
        search=None,
        search_in='all',
        groupby=None,
        **kwargs,
    ):
        """Site Attendance history hub — filters, sort, search, pagination."""
        values = self._prepare_attendance_history_values(
            page=page,
            sortby=sortby,
            filterby=filterby,
            search=search,
            search_in=search_in,
            groupby=groupby,
            **kwargs,
        )
        return request.render('construction_hrd.portal_attendance_history', values)

    @http.route(
        '/my/cems/attendance/history',
        type='http',
        auth='user',
        website=True,
    )
    def portal_attendance_history(self, **kwargs):
        """Back-compat alias → main Site Attendance page."""
        return request.redirect_query('/my/cems/attendance', query=kwargs, code=301)

    @http.route(
        '/my/cems/attendance/check_in',
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def portal_check_in(self, **post):
        employee = self._cems_get_employee()
        next_url = post.get('next') or '/my'
        if not employee:
            return self._attendance_redirect(error='no_employee', next_url=next_url)
        self._ensure_own_employee(employee)

        gps = self._parse_required_gps(post)
        if gps is None:
            return self._attendance_redirect(error='invalid_gps', next_url=next_url)
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
            return self._attendance_redirect(error='outside_geofence', next_url=next_url)
        except UserError as err:
            _logger.warning(
                'CEMS portal check-in failed for employee=%s: %s',
                employee.id,
                err.args[0] if err.args else err,
            )
            return self._attendance_redirect(error='check_in_failed', next_url=next_url)
        except Exception:
            _logger.exception(
                'CEMS portal check-in unexpected error for employee=%s',
                employee.id,
            )
            return self._attendance_redirect(error='check_in_failed', next_url=next_url)

        return self._attendance_redirect(success='checked_in', next_url=next_url)

    @http.route(
        '/my/cems/attendance/check_out',
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def portal_check_out(self, **post):
        employee = self._cems_get_employee()
        next_url = post.get('next') or '/my'
        if not employee:
            return self._attendance_redirect(error='checkout_failed', next_url=next_url)
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
            return self._attendance_redirect(error='checkout_failed', next_url=next_url)
        except Exception:
            _logger.exception(
                'CEMS portal check-out unexpected error for employee=%s',
                employee.id,
            )
            return self._attendance_redirect(error='checkout_failed', next_url=next_url)

        return self._attendance_redirect(success='checked_out', next_url=next_url)

    @http.route(
        '/my/cems/attendance/json/check_in',
        type='jsonrpc',
        auth='user',
    )
    def portal_check_in_json(self, latitude, longitude, selfie_b64=None, filename=None):
        employee = self._cems_get_employee()
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
