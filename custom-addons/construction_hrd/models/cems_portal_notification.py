# -*- coding: utf-8 -*-
from markupsafe import Markup, escape

from odoo import _, api, fields, models


class CemsPortalNotification(models.Model):
    """In-app portal notification feed (bell on /my).

    Complements native ``message_notify`` (email / Discuss Inbox). Portal users
    cannot use Discuss Inbox, so this model powers the CEMS hub bell.
    """

    _name = 'cems.portal.notification'
    _description = 'CEMS Portal Notification'
    _order = 'create_date desc, id desc'

    user_id = fields.Many2one(
        'res.users',
        string='Recipient',
        required=True,
        index=True,
        ondelete='cascade',
    )
    title = fields.Char(required=True)
    body = fields.Char()
    notification_type = fields.Selection(
        selection=[
            ('project', 'Project'),
            ('task', 'Task'),
            ('gate', 'Gate Pass'),
            ('attendance', 'Attendance'),
            ('system', 'System'),
        ],
        string='Type',
        default='system',
        required=True,
        index=True,
    )
    url = fields.Char(string='Link')
    is_read = fields.Boolean(default=False, index=True)
    res_model = fields.Char(index=True)
    res_id = fields.Integer(index=True)

    @api.model
    def _cems_relative_time(self, dt):
        if not dt:
            return ''
        when = fields.Datetime.to_datetime(dt)
        now = fields.Datetime.now()
        seconds = int((now - when).total_seconds())
        if seconds < 45:
            return _('Just now')
        if seconds < 3600:
            minutes = max(1, seconds // 60)
            return _('%s minutes ago', minutes)
        if seconds < 86400:
            hours = max(1, seconds // 3600)
            return _('%s hours ago', hours)
        if seconds < 172800:
            return _('Yesterday')
        days = max(1, seconds // 86400)
        if days < 7:
            return _('%s days ago', days)
        return fields.Date.to_string(when.date())

    @api.model
    def _cems_portal_feed_for_user(self, user=None, limit=20):
        """Values for the hub notification panel."""
        user = user or self.env.user
        if not user or user._is_public():
            return {
                'items': [],
                'unread_count': 0,
                'head_meta': _('No notifications'),
            }
        Notification = self.sudo()
        domain = [('user_id', '=', user.id)]
        unread_count = Notification.search_count(domain + [('is_read', '=', False)])
        records = Notification.search(domain, limit=limit)
        items = []
        for rec in records:
            items.append({
                'id': rec.id,
                'title': rec.title,
                'body': rec.body or '',
                'type': rec.notification_type,
                'url': rec.url or '#',
                'is_read': rec.is_read,
                'time_label': self._cems_relative_time(rec.create_date),
            })
        if unread_count:
            head_meta = _('%s new', unread_count)
        elif items:
            head_meta = _('All caught up')
        else:
            head_meta = _('No notifications')
        return {
            'items': items,
            'unread_count': unread_count,
            'head_meta': head_meta,
        }

    @api.model
    def _cems_notify_users(
        self,
        users,
        *,
        title,
        body='',
        notification_type='system',
        url=False,
        res_model=False,
        res_id=False,
        mail_record=None,
        mail_subject=False,
    ):
        """Create portal feed rows and optionally push native mail notifications."""
        if self.env.context.get('cems_skip_portal_notify') or self.env.context.get(
            'mail_auto_subscribe_no_notify'
        ):
            return self.browse()
        users = (users or self.env['res.users']).filtered(
            lambda u: u.active and not u._is_public()
        ) - self.env.user
        if not users:
            return self.browse()

        Notification = self.sudo()
        created = Notification
        vals_list = []
        for user in users:
            vals_list.append({
                'user_id': user.id,
                'title': title,
                'body': body or False,
                'notification_type': notification_type,
                'url': url or False,
                'res_model': res_model or False,
                'res_id': res_id or False,
            })
        if vals_list:
            created = Notification.create(vals_list)

        if mail_record is not None and hasattr(mail_record, 'message_notify'):
            model_description = self.env['ir.model']._get(mail_record._name).display_name
            subject = mail_subject or title
            for user in users:
                if not user.partner_id:
                    continue
                mail_body = Markup('<p>%s</p>') % escape(body or title)
                if url:
                    mail_body = Markup('%s<p><a href="%s">%s</a></p>') % (
                        mail_body,
                        escape(url),
                        escape(_('Open')),
                    )
                mail_record.message_notify(
                    subject=subject,
                    body=mail_body,
                    partner_ids=user.partner_id.ids,
                    email_layout_xmlid='mail.mail_notification_layout',
                    model_description=model_description,
                    mail_auto_delete=False,
                )
        return created

    def action_mark_read(self):
        self.sudo().write({'is_read': True})
        return True

    @api.model
    def action_mark_all_read(self, user=None):
        user = user or self.env.user
        unread = self.sudo().search([
            ('user_id', '=', user.id),
            ('is_read', '=', False),
        ])
        unread.write({'is_read': True})
        return True
