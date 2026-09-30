# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class CemsPortalNotifications(http.Controller):
    """JSON-RPC endpoints for the portal hub notification bell."""

    @http.route(
        '/my/cems/notifications/mark_read',
        type='jsonrpc',
        auth='user',
        website=True,
    )
    def mark_read(self, notification_ids=None, **kwargs):
        ids = notification_ids or []
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        ids = [int(i) for i in ids if i]
        notifications = request.env['cems.portal.notification'].sudo().search([
            ('id', 'in', ids),
            ('user_id', '=', request.env.user.id),
        ])
        notifications.action_mark_read()
        unread = request.env['cems.portal.notification'].sudo().search_count([
            ('user_id', '=', request.env.user.id),
            ('is_read', '=', False),
        ])
        return {'ok': True, 'unread_count': unread}

    @http.route(
        '/my/cems/notifications/mark_all_read',
        type='jsonrpc',
        auth='user',
        website=True,
    )
    def mark_all_read(self, **kwargs):
        request.env['cems.portal.notification'].action_mark_all_read()
        return {'ok': True, 'unread_count': 0}
